import tempfile
from pathlib import Path

import httpx

from app.core.config import Settings
from app.core.errors import ConfigurationError, WhatsAppProcessingError


class MetaWhatsAppClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _token(self) -> str:
        if self.settings.whatsapp_access_token is None:
            raise ConfigurationError("WHATSAPP_ACCESS_TOKEN is not configured.")
        return self.settings.whatsapp_access_token.get_secret_value()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token()}"}

    def download_media(self, media_id: str) -> str:
        base = f"https://graph.facebook.com/{self.settings.whatsapp_graph_version}"
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                metadata_response = client.get(f"{base}/{media_id}", headers=self._headers())
                metadata_response.raise_for_status()
                media_url = metadata_response.json()["url"]
                media_response = client.get(media_url, headers=self._headers(), follow_redirects=True)
                media_response.raise_for_status()
                if len(media_response.content) > self.settings.max_image_bytes:
                    raise WhatsAppProcessingError("WhatsApp media exceeds the maximum image size.")
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            raise WhatsAppProcessingError("Failed to download WhatsApp image media.") from exc

        content_type = media_response.headers.get("content-type", "image/jpeg").split(";")[0]
        suffix = {"image/png": ".png", "image/webp": ".webp"}.get(content_type, ".jpg")
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp.write(media_response.content)
        temp.close()
        return temp.name

    def send_text(self, recipient: str, text: str) -> None:
        if not self.settings.whatsapp_phone_number_id:
            raise ConfigurationError("WHATSAPP_PHONE_NUMBER_ID is not configured.")
        url = (
            f"https://graph.facebook.com/{self.settings.whatsapp_graph_version}/"
            f"{self.settings.whatsapp_phone_number_id}/messages"
        )
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(
                    url,
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WhatsAppProcessingError("Failed to send WhatsApp reply.") from exc

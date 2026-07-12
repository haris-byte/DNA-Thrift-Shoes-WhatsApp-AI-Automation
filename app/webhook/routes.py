import logging
import os

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.models.api_models import WebhookAcknowledgement
from app.models.meta_webhook_models import MetaWebhookPayload
from app.models.webhook_models import IncomingMessage, MessageType


logger = logging.getLogger(__name__)
router = APIRouter(tags=["WhatsApp"])


@router.get("/webhook", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    request: Request,
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> PlainTextResponse:
    settings = request.app.state.container.settings
    expected = settings.whatsapp_verify_token.get_secret_value()
    if hub_mode == "subscribe" and hub_verify_token == expected and hub_challenge is not None:
        logger.info("meta_webhook_verification_success")
        return PlainTextResponse(hub_challenge)
    logger.warning("meta_webhook_verification_failed")
    raise HTTPException(status_code=403, detail="Webhook verification failed.")


@router.post("/webhook", response_model=WebhookAcknowledgement)
def receive_whatsapp_webhook(
    payload: MetaWebhookPayload,
    request: Request,
) -> WebhookAcknowledgement:
    container = request.app.state.container
    messages_received = 0
    replies_sent = 0

    for entry in payload.entry:
        for change in entry.changes:
            for message in change.value.messages:
                messages_received += 1
                if container.engine.idempotency.get(message.id) is not None:
                    logger.info("duplicate_meta_message_ignored message_id=%s", message.id)
                    continue
                temp_path: str | None = None
                try:
                    if message.type == "text":
                        internal = IncomingMessage(
                            sender_id=message.sender,
                            message_id=message.id,
                            message_type=MessageType.TEXT,
                            text=message.text.body if message.text else None,
                        )
                    else:
                        if message.image is None:
                            continue
                        temp_path = container.meta_client.download_media(message.image.id)
                        internal = IncomingMessage(
                            sender_id=message.sender,
                            message_id=message.id,
                            message_type=MessageType.IMAGE,
                            text=message.image.caption,
                            image_source=temp_path,
                            image_media_id=message.image.id,
                        )

                    response = container.engine.handle(internal)
                    if not response.duplicate_delivery:
                        container.meta_client.send_text(message.sender, response.reply)
                        replies_sent += 1
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.unlink(temp_path)

    return WebhookAcknowledgement(
        entries_received=len(payload.entry),
        messages_received=messages_received,
        replies_sent=replies_sent,
    )

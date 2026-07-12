import base64
import io
import ipaddress
import socket
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.errors import ImageDownloadError, UnsupportedImageError


@dataclass(frozen=True)
class ImageAsset:
    data: bytes
    mime_type: str
    source_name: str

    def to_data_url(self) -> str:
        encoded = base64.b64encode(self.data).decode("ascii")
        return f"data:{self.mime_type};base64,{encoded}"


class ImageLoader:
    ALLOWED_FORMATS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _validate(self, data: bytes, source_name: str) -> ImageAsset:
        if not data:
            raise UnsupportedImageError("The image is empty.")
        if len(data) > self.settings.max_image_bytes:
            raise UnsupportedImageError("The image exceeds the maximum allowed size.")
        try:
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
                image_format = image.format
        except (UnidentifiedImageError, OSError) as exc:
            raise UnsupportedImageError("The supplied file is not a valid readable image.") from exc
        if image_format not in self.ALLOWED_FORMATS:
            raise UnsupportedImageError(f"Unsupported image format: {image_format or 'unknown'}.")
        return ImageAsset(data=data, mime_type=self.ALLOWED_FORMATS[image_format], source_name=source_name)

    @staticmethod
    def _validate_remote_url(source: str) -> None:
        parsed = urlparse(source)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ImageDownloadError("Only valid HTTP/HTTPS image URLs are accepted.")
        try:
            addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ImageDownloadError("The image hostname could not be resolved.") from exc
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise ImageDownloadError("Private or local-network image URLs are not allowed.")

    def _download(self, source: str) -> bytes:
        current_url = source
        try:
            with httpx.Client(
                timeout=self.settings.request_timeout_seconds,
                follow_redirects=False,
            ) as client:
                for _ in range(4):
                    self._validate_remote_url(current_url)
                    with client.stream("GET", current_url) as response:
                        if response.status_code in {301, 302, 303, 307, 308}:
                            location = response.headers.get("location")
                            if not location:
                                raise ImageDownloadError("Image redirect did not include a destination.")
                            current_url = urljoin(current_url, location)
                            continue

                        response.raise_for_status()
                        content_type = response.headers.get("content-type", "").split(";")[0].lower()
                        if content_type and content_type not in self.ALLOWED_FORMATS.values():
                            raise UnsupportedImageError(
                                f"Remote resource is not a supported image: {content_type}."
                            )

                        chunks: list[bytes] = []
                        total = 0
                        for chunk in response.iter_bytes():
                            total += len(chunk)
                            if total > self.settings.max_image_bytes:
                                raise UnsupportedImageError(
                                    "The image exceeds the maximum allowed size."
                                )
                            chunks.append(chunk)
                        return b"".join(chunks)

                raise ImageDownloadError("The image URL redirected too many times.")
        except (UnsupportedImageError, ImageDownloadError):
            raise
        except httpx.HTTPError as exc:
            raise ImageDownloadError("The image URL could not be downloaded.") from exc

    def load(self, source: str) -> ImageAsset:
        if source.startswith(("http://", "https://")):
            return self._validate(self._download(source), source)
        path = Path(source)
        if not path.is_file():
            raise UnsupportedImageError("The local image file does not exist.")
        return self._validate(path.read_bytes(), path.name)

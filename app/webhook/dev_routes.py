import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.errors import UnsupportedImageError
from app.models.conversation_models import BotResponse
from app.models.webhook_models import DevWebhookPayload, IncomingMessage, MessageType


router = APIRouter(prefix="/dev", tags=["Development"])


@router.post("/webhook", response_model=BotResponse)
def receive_dev_webhook(payload: DevWebhookPayload, request: Request) -> BotResponse:
    return request.app.state.container.engine.handle(payload.to_internal())


@router.post("/upload", response_model=BotResponse)
async def receive_uploaded_image(
    request: Request,
    sender_id: Annotated[str, Form(min_length=1, max_length=128)],
    message_id: Annotated[str, Form(min_length=1, max_length=200)],
    image: Annotated[UploadFile, File(description="Real shoe or size-tag image")],
) -> BotResponse:
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    if image.content_type not in allowed:
        raise UnsupportedImageError("Only JPEG, PNG, and WEBP images are accepted.")

    data = await image.read()
    settings = request.app.state.container.settings
    if len(data) > settings.max_image_bytes:
        raise UnsupportedImageError("The image exceeds the maximum allowed size.")

    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=allowed[image.content_type]) as temp:
            temp.write(data)
            temp_path = temp.name
        message = IncomingMessage(
            sender_id=sender_id,
            message_id=message_id,
            message_type=MessageType.IMAGE,
            image_source=temp_path,
        )
        return request.app.state.container.engine.handle(message)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

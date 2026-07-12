from enum import Enum
from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.models.base import InternalModel


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"


class IncomingMessage(InternalModel):
    sender_id: str = Field(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_+.\-]+$")
    message_id: str = Field(..., min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_+.\-:]+$")
    message_type: MessageType
    text: Optional[str] = Field(default=None, max_length=4096)
    image_source: Optional[str] = Field(default=None, max_length=4096)
    image_media_id: Optional[str] = Field(default=None, max_length=200)

    @field_validator("text", "image_source", "image_media_id")
    @classmethod
    def blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_content(self) -> "IncomingMessage":
        if self.message_type == MessageType.TEXT and self.text is None:
            raise ValueError("Text message requires non-empty text.")
        if self.message_type == MessageType.IMAGE and not (self.image_source or self.image_media_id):
            raise ValueError("Image message requires image_source or image_media_id.")
        return self


class DevWebhookPayload(InternalModel):
    sender_id: str = Field(..., min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_+.\-]+$")
    message_id: str = Field(..., min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_+.\-:]+$")
    message_type: MessageType
    text: Optional[str] = Field(default=None, max_length=4096)
    image_url: Optional[str] = Field(default=None, max_length=4096)

    @field_validator("text", "image_url")
    @classmethod
    def blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_content(self) -> "DevWebhookPayload":
        if self.message_type == MessageType.TEXT and self.text is None:
            raise ValueError("Text message requires non-empty text.")
        if self.message_type == MessageType.IMAGE and self.image_url is None:
            raise ValueError("Image message requires image_url.")
        return self

    def to_internal(self) -> IncomingMessage:
        return IncomingMessage(
            sender_id=self.sender_id,
            message_id=self.message_id,
            message_type=self.message_type,
            text=self.text,
            image_source=self.image_url,
        )

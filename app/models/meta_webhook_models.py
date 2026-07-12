from typing import Literal, Optional

from pydantic import Field, model_validator

from app.models.base import ExternalProviderModel


class MetaTextContent(ExternalProviderModel):
    body: str = Field(..., min_length=1, max_length=4096)


class MetaImageContent(ExternalProviderModel):
    id: str = Field(..., min_length=1, max_length=200)
    mime_type: str = Field(..., min_length=1, max_length=100)
    sha256: Optional[str] = Field(default=None, max_length=200)
    caption: Optional[str] = Field(default=None, max_length=4096)


class MetaMessage(ExternalProviderModel):
    sender: str = Field(alias="from", min_length=1, max_length=128)
    id: str = Field(..., min_length=1, max_length=200)
    timestamp: str = Field(..., min_length=1, max_length=30)
    type: Literal["text", "image"]
    text: Optional[MetaTextContent] = None
    image: Optional[MetaImageContent] = None

    @model_validator(mode="after")
    def validate_content(self) -> "MetaMessage":
        if self.type == "text" and self.text is None:
            raise ValueError("Meta text message requires text content.")
        if self.type == "image" and self.image is None:
            raise ValueError("Meta image message requires image metadata.")
        return self


class MetaStatus(ExternalProviderModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str


class MetaMetadata(ExternalProviderModel):
    display_phone_number: str
    phone_number_id: str


class MetaWebhookValue(ExternalProviderModel):
    messaging_product: Literal["whatsapp"]
    metadata: MetaMetadata
    messages: list[MetaMessage] = Field(default_factory=list)
    statuses: list[MetaStatus] = Field(default_factory=list)


class MetaChange(ExternalProviderModel):
    value: MetaWebhookValue
    field: Literal["messages"]


class MetaEntry(ExternalProviderModel):
    id: str
    changes: list[MetaChange]


class MetaWebhookPayload(ExternalProviderModel):
    object: Literal["whatsapp_business_account"]
    entry: list[MetaEntry]

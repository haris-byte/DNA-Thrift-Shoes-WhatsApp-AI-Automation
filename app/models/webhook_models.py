from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator

class WhatsAppWebhookPayload(BaseModel):
    sender_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    message_type: Literal["text", "image"]
    text: Optional[str] = None
    image_url: Optional[str] = None
    
    @model_validator(mode="after")
    def validate_message_content(self):
        if self.message_type == "text" and not self.text:
            raise ValueError("Text message must include text.")

        if self.message_type == "image" and not self.image_url:
            raise ValueError("Image message must include image_url.")

        return self
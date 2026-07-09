from typing import Optional, Literal
from pydantic import BaseModel, Field

class WhatsAppWebhookPayload(BaseModel):
    sender_id: str = Field(..., min_length=1)
    message_id: str = Field(..., min_length=1)
    message_type: Literal["text", "image"]
    text: Optional[str] = None
    image_url: Optional[str] = None
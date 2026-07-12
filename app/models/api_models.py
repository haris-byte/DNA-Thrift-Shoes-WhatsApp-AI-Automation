from typing import Literal

from pydantic import Field

from app.models.base import InternalModel


class HealthResponse(InternalModel):
    status: Literal["running"] = "running"
    application: str
    version: str
    environment: str


class WebhookAcknowledgement(InternalModel):
    status: Literal["accepted"] = "accepted"
    entries_received: int = Field(..., ge=0)
    messages_received: int = Field(..., ge=0)
    replies_sent: int = Field(..., ge=0)

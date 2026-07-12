from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from app.models.base import InternalModel
from app.models.inventory_models import InventoryMatchResult
from app.models.shoe_models import ShoeQuery


class ConversationState(str, Enum):
    AWAITING_QUERY = "AWAITING_QUERY"
    IDENTIFYING_SHOE = "IDENTIFYING_SHOE"
    AWAITING_SIZE_CONFIRMATION = "AWAITING_SIZE_CONFIRMATION"
    PRESENTING_RESULT = "PRESENTING_RESULT"
    AWAITING_PURCHASE_INTENT = "AWAITING_PURCHASE_INTENT"
    FALLBACK_HUMAN = "FALLBACK_HUMAN"


class ConversationSession(InternalModel):
    sender_id: str = Field(..., min_length=1, max_length=128)
    state: ConversationState = ConversationState.AWAITING_QUERY
    pending_query: Optional[ShoeQuery] = None
    last_inventory_result: Optional[InventoryMatchResult] = None
    failed_clarification_attempts: int = Field(default=0, ge=0, le=20)
    last_clarification_question: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_state(self) -> "ConversationSession":
        if self.state in {
            ConversationState.AWAITING_SIZE_CONFIRMATION,
            ConversationState.AWAITING_PURCHASE_INTENT,
        } and self.pending_query is None:
            raise ValueError(f"{self.state.value} requires pending_query.")
        if (
            self.state == ConversationState.AWAITING_SIZE_CONFIRMATION
            and self.pending_query is not None
            and self.pending_query.size_us is not None
        ):
            raise ValueError("AWAITING_SIZE_CONFIRMATION requires missing size_us.")
        return self


class BotResponse(InternalModel):
    sender_id: str = Field(..., min_length=1, max_length=128)
    message_id: str = Field(..., min_length=1, max_length=200)
    state: ConversationState
    reply: str = Field(..., min_length=1, max_length=2500)
    session: ConversationSession
    duplicate_delivery: bool = False

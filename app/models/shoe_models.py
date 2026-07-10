from typing import Optional
from pydantic import BaseModel, Field


class ShoeQuery(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    size_us: Optional[float] = None
    condition_score: Optional[int] = Field(default=None, ge=1, le=10)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "text"

class TextParserResult(BaseModel):
    query: ShoeQuery
    missing_fields: list[str]
    clarification_needed: bool
    clarification_question: Optional[str] = None
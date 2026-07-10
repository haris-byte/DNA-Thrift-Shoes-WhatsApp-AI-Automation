from enum import Enum
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


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    SOLD_OUT = "sold_out"


class InventoryItem(BaseModel):
    product_id: str
    product_name: str
    brand: str
    model: str
    size_us: float
    condition_score: int = Field(..., ge=1, le=10)
    base_price: int = Field(..., gt=0)
    stock_status: StockStatus
    description: str


class PriceBreakdown(BaseModel):
    base_price: int
    condition_score: int
    condition_multiplier: float
    final_price: int
    currency: str = "PKR"


class MatchType(str, Enum):
    EXACT = "exact_match"
    PARTIAL = "partial_match"
    NO_MATCH = "no_match"


class InventoryMatchResult(BaseModel):
    match_type: MatchType
    query: ShoeQuery
    exact_match: Optional[InventoryItem] = None
    alternatives: list[InventoryItem] = Field(default_factory=list)
    price: Optional[PriceBreakdown] = None
    message: str
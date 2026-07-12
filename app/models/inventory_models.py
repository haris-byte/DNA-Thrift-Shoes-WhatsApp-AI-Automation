from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from app.models.base import InternalModel
from app.models.shoe_models import ShoeQuery


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    SOLD_OUT = "sold_out"


class InventoryItem(InternalModel):
    product_id: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=200)
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=150)
    size_us: float = Field(..., ge=3, le=18)
    condition_score: int = Field(..., ge=1, le=10)
    base_price: int = Field(..., gt=0, le=5_000_000)
    stock_status: StockStatus
    description: str = Field(..., min_length=1, max_length=1000)


class PriceBreakdown(InternalModel):
    base_price: int = Field(..., gt=0)
    condition_score: int = Field(..., ge=1, le=10)
    condition_multiplier: float = Field(..., gt=0, le=1.0)
    final_price: int = Field(..., gt=0)
    currency: str = Field(default="PKR", min_length=3, max_length=3)


class MatchType(str, Enum):
    EXACT = "exact_match"
    PARTIAL = "partial_match"
    NO_MATCH = "no_match"


class InventoryMatchResult(InternalModel):
    match_type: MatchType
    query: ShoeQuery
    exact_match: Optional[InventoryItem] = None
    alternatives: list[InventoryItem] = Field(default_factory=list, max_length=5)
    price: Optional[PriceBreakdown] = None
    message: str = Field(..., min_length=1, max_length=2500)

    @model_validator(mode="after")
    def validate_match_consistency(self) -> "InventoryMatchResult":
        if self.match_type == MatchType.EXACT:
            if self.exact_match is None or self.price is None:
                raise ValueError("Exact match requires exact_match and price.")
        elif self.match_type == MatchType.PARTIAL:
            if not self.alternatives:
                raise ValueError("Partial match requires alternatives.")
            if self.exact_match is not None:
                raise ValueError("Partial match cannot include exact_match.")
        elif self.match_type == MatchType.NO_MATCH and self.exact_match is not None:
            raise ValueError("No-match cannot include exact_match.")
        return self

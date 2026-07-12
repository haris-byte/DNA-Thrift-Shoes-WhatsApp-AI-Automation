from enum import Enum
from typing import Optional

from pydantic import Field, model_validator

from app.models.base import InternalModel


class SizeSystem(str, Enum):
    US = "US"
    UK = "UK"
    EU = "EU"
    UNKNOWN = "UNKNOWN"


class DetectedSize(InternalModel):
    system: SizeSystem
    value: float = Field(..., gt=0, le=60)
    us_estimate: Optional[float] = Field(default=None, ge=3, le=18)
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_confirmation: bool = False
    source_text: str = Field(..., min_length=1, max_length=200)


class OCRDetection(InternalModel):
    text: str = Field(..., min_length=1, max_length=300)
    confidence: float = Field(..., ge=0.0, le=1.0)


class OCRResult(InternalModel):
    raw_text: str = Field(default="", max_length=5000)
    detections: list[OCRDetection] = Field(default_factory=list)
    size_candidates: list[DetectedSize] = Field(default_factory=list)
    selected_size: Optional[DetectedSize] = None
    readable: bool = False

    @model_validator(mode="after")
    def validate_consistency(self) -> "OCRResult":
        if self.readable and self.selected_size is None:
            raise ValueError("Readable OCR result requires selected_size.")
        if not self.readable and self.selected_size is not None:
            raise ValueError("Unreadable OCR result cannot include selected_size.")
        return self


class VisionAnalysisResult(InternalModel):
    brand: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=150)
    style_family: Optional[str] = Field(default=None, max_length=150)
    condition_score: Optional[int] = Field(default=None, ge=1, le=10)
    condition_notes: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    visible_size_text: Optional[str] = Field(default=None, max_length=300)
    provider_model: Optional[str] = Field(default=None, max_length=200)


class ShoeQuery(InternalModel):
    brand: Optional[str] = Field(default=None, min_length=1, max_length=100)
    model: Optional[str] = Field(default=None, min_length=1, max_length=150)
    size_us: Optional[float] = Field(default=None, ge=3, le=18)
    condition_score: Optional[int] = Field(default=None, ge=1, le=10)
    condition_notes: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = Field(default="unknown", min_length=1, max_length=120)


class TextParserResult(InternalModel):
    query: ShoeQuery
    missing_fields: list[str] = Field(default_factory=list)
    clarification_needed: bool
    clarification_question: Optional[str] = Field(default=None, max_length=1000)
    used_llm: bool = False


class PhotoAnalysisResult(InternalModel):
    vision: VisionAnalysisResult
    ocr: OCRResult
    query: ShoeQuery
    missing_fields: list[str] = Field(default_factory=list)
    clarification_needed: bool
    clarification_question: Optional[str] = Field(default=None, max_length=1000)

from typing import Optional

from pydantic import Field

from app.models.base import InternalModel


class ErrorDetail(InternalModel):
    field: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=1000)
    error_type: str = Field(..., min_length=1, max_length=200)


class ErrorBody(InternalModel):
    code: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=1000)
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(InternalModel):
    error: ErrorBody

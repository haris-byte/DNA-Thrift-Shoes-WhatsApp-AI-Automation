from pydantic import BaseModel, ConfigDict


class InternalModel(BaseModel):
    """Strict model for data controlled by this application."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=False,
    )


class ExternalProviderModel(BaseModel):
    """Model for third-party payloads where providers may add fields."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

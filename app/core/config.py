from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DNA Thrift WhatsApp AI"
    app_version: str = "1.0.0"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_path: Path = Path("data/dna_thrift.db")
    max_clarification_attempts: int = Field(default=2, ge=1, le=5)
    max_image_bytes: int = Field(default=8_000_000, ge=100_000, le=20_000_000)
    request_timeout_seconds: float = Field(default=30.0, gt=1, le=120)

    whatsapp_verify_token: SecretStr = SecretStr("change-me")
    whatsapp_access_token: Optional[SecretStr] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_graph_version: str = "v25.0"

    openrouter_api_key: Optional[SecretStr] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    vision_model: str = "openrouter/free"
    nlp_model: str = "openrouter/free"
    enable_llm_nlp: bool = True
    openrouter_http_referer: Optional[str] = None
    openrouter_app_title: str = "DNA Thrift WhatsApp AI"

    enable_easyocr: bool = True
    easyocr_gpu: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def whatsapp_is_configured(self) -> bool:
        return bool(self.whatsapp_access_token and self.whatsapp_phone_number_id)

    @property
    def vision_is_configured(self) -> bool:
        return self.openrouter_api_key is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()

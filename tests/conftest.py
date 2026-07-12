from pathlib import Path

import pytest

from app.core.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_path=tmp_path / "test.db",
        whatsapp_verify_token="test-token",
        enable_llm_nlp=False,
        enable_easyocr=False,
        openrouter_api_key=None,
    )

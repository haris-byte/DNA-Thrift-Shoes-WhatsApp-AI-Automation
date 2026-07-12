import io
import json

from PIL import Image

from app.core.config import Settings
from app.vision.image_io import ImageAsset
from app.vision.vlm import OpenRouterVisionAnalyzer


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self):
        return {
            "model": "qwen/test-vision",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "brand": "Nike",
                                "model": "Air Force 1",
                                "style_family": "low-top sneaker",
                                "condition_score": 7,
                                "condition_notes": ["toe-box creasing"],
                                "confidence": 0.9,
                                "visible_size_text": "US 10",
                            }
                        )
                    }
                }
            ],
        }


class FakeClient:
    last_json = None

    def __init__(self, timeout: float):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url: str, headers: dict[str, str], json: dict):
        FakeClient.last_json = json
        return FakeResponse()


def test_openrouter_vision_adapter_uses_real_image_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.vision.vlm.httpx.Client", FakeClient)
    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buffer, format="PNG")
    settings = Settings(
        environment="test",
        database_path=tmp_path / "vlm.db",
        openrouter_api_key="test-key",
        vision_model="qwen/test-vision",
        enable_llm_nlp=False,
    )
    result = OpenRouterVisionAnalyzer(settings).analyze(
        ImageAsset(data=buffer.getvalue(), mime_type="image/png", source_name="test.png")
    )
    assert result.model == "Air Force 1"
    assert result.condition_score == 7
    assert result.provider_model == "qwen/test-vision"
    content = FakeClient.last_json["messages"][0]["content"]
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert FakeClient.last_json["response_format"]["type"] == "json_schema"

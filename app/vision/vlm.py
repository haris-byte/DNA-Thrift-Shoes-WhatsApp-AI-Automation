import json
import httpx

from app.core.config import Settings
from app.core.errors import ConfigurationError, VisionProcessingError
from app.models.shoe_models import VisionAnalysisResult
from app.vision.image_io import ImageAsset


class OpenRouterVisionAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, asset: ImageAsset) -> VisionAnalysisResult:
        if self.settings.openrouter_api_key is None:
            raise ConfigurationError(
                "Real shoe recognition requires OPENROUTER_API_KEY. "
                "Set it in .env before processing photo queries."
            )

        schema: dict[str, object] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "brand": {"type": ["string", "null"]},
                "model": {"type": ["string", "null"]},
                "style_family": {"type": ["string", "null"]},
                "condition_score": {"type": ["integer", "null"], "minimum": 1, "maximum": 10},
                "condition_notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 8,
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "visible_size_text": {"type": ["string", "null"]},
            },
            "required": [
                "brand",
                "model",
                "style_family",
                "condition_score",
                "condition_notes",
                "confidence",
                "visible_size_text",
            ],
        }

        prompt = (
            "Analyze this thrift-shoe photo. Identify the visible brand and exact model only when evidence is strong. "
            "If the exact model is uncertain, return null for model and provide only a style_family. "
            "Assess visible condition from wear, creasing, sole wear, staining, tears, and upper damage on a 1-10 scale. "
            "Do not infer size unless readable text is actually visible. Do not invent colorways or authenticity claims."
        )

        request_body = {
            "model": self.settings.vision_model,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": asset.to_data_url()}},
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "shoe_vision_analysis",
                    "strict": True,
                    "schema": schema,
                },
            },
            "plugins": [{"id": "response-healing"}],
        }

        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": self.settings.openrouter_app_title,
        }
        if self.settings.openrouter_http_referer:
            headers["HTTP-Referer"] = self.settings.openrouter_http_referer

        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(
                    f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=request_body,
                )
                response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            provider_model = str(body.get("model", self.settings.vision_model))
            if isinstance(content, list):
                text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
                content = "".join(text_parts)
            if not isinstance(content, str):
                raise ValueError("Unexpected VLM response content type.")
            parsed = json.loads(content)
            return VisionAnalysisResult(
                brand=parsed.get("brand"),
                model=parsed.get("model"),
                style_family=parsed.get("style_family"),
                condition_score=parsed.get("condition_score"),
                condition_notes=parsed.get("condition_notes", []),
                confidence=parsed.get("confidence", 0.0),
                visible_size_text=parsed.get("visible_size_text"),
                provider_model=provider_model,
            )
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise VisionProcessingError(f"Vision provider returned an error: {detail}") from exc
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise VisionProcessingError("Vision model response could not be validated.") from exc

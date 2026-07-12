import json
import re
from typing import Optional

import httpx

from app.core.config import Settings
from app.core.errors import LLMProcessingError
from app.models.shoe_models import ShoeQuery, TextParserResult


BRAND_KEYWORDS: dict[str, str] = {
    "new balance": "New Balance",
    "air jordan": "Nike",
    "jordan": "Nike",
    "air force": "Nike",
    "af1": "Nike",
    "dunk": "Nike",
    "nike": "Nike",
    "adidas": "Adidas",
    "yeezy": "Adidas",
    "ultraboost": "Adidas",
    "puma": "Puma",
    "reebok": "Reebok",
    "vans": "Vans",
    "converse": "Converse",
}

MODEL_KEYWORDS: dict[str, str] = {
    "new balance 550": "New Balance 550",
    "air jordan 1": "Air Jordan 1",
    "jordan 1": "Air Jordan 1",
    "air force 1": "Air Force 1",
    "airforce 1": "Air Force 1",
    "af1": "Air Force 1",
    "dunk low": "Dunk Low",
    "air max": "Air Max",
    "yeezy": "Yeezy",
    "ultraboost": "Ultraboost",
    "stan smith": "Stan Smith",
    "superstar": "Superstar",
    "old skool": "Old Skool",
    "chuck taylor": "Chuck Taylor",
    "puma suede": "Puma Suede",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"\b{re.escape(phrase.lower())}\b", text) is not None


def extract_brand(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    for keyword, brand in sorted(BRAND_KEYWORDS.items(), key=lambda item: len(item[0]), reverse=True):
        if contains_phrase(normalized, keyword):
            return brand
    return None


def extract_model(text: str) -> Optional[str]:
    normalized = normalize_text(text)
    for keyword, model in sorted(MODEL_KEYWORDS.items(), key=lambda item: len(item[0]), reverse=True):
        if contains_phrase(normalized, keyword):
            return model
    return None


def extract_size(text: str) -> Optional[float]:
    normalized = normalize_text(text)
    patterns = [
        r"\b(?:us|usa|size)\s*[:#-]?\s*(\d{1,2}(?:\.5)?)\b",
        r"\b(\d{1,2}(?:\.5)?)\s*(?:us)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            size = float(match.group(1))
            return size if 3 <= size <= 18 else None
    if re.fullmatch(r"\s*(\d{1,2}(?:\.5)?)\s*", normalized):
        size = float(normalized)
        return size if 3 <= size <= 18 else None
    return None


def calculate_confidence(brand: Optional[str], model: Optional[str], size_us: Optional[float]) -> float:
    return round((0.3 if brand else 0.0) + (0.4 if model else 0.0) + (0.3 if size_us else 0.0), 2)


def missing_fields_for(query: ShoeQuery) -> list[str]:
    missing: list[str] = []
    if query.brand is None:
        missing.append("brand")
    if query.model is None:
        missing.append("model")
    if query.size_us is None:
        missing.append("size_us")
    return missing


def build_clarification(missing_fields: list[str]) -> str:
    field_set = set(missing_fields)
    if field_set == {"brand", "model", "size_us"}:
        return "Please share the shoe brand, exact model, and US size, or send a clear shoe photo."
    if "model" in field_set and "size_us" in field_set:
        return "Which exact shoe model and US size are you looking for?"
    if field_set == {"size_us"}:
        return "What US size are you looking for? Please reply like: US 10."
    if field_set == {"model"}:
        return "Which exact shoe model are you looking for?"
    if field_set == {"brand"}:
        return "Which shoe brand are you looking for?"
    return "Please provide the missing shoe details: " + ", ".join(missing_fields) + "."


class RuleTextParser:
    def parse(self, text: str) -> TextParserResult:
        brand = extract_brand(text)
        model = extract_model(text)
        size_us = extract_size(text)
        query = ShoeQuery(
            brand=brand,
            model=model,
            size_us=size_us,
            confidence=calculate_confidence(brand, model, size_us),
            source="rule_parser",
        )
        missing = missing_fields_for(query)
        return TextParserResult(
            query=query,
            missing_fields=missing,
            clarification_needed=bool(missing),
            clarification_question=build_clarification(missing) if missing else None,
            used_llm=False,
        )


class OpenRouterTextExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def configured(self) -> bool:
        return self.settings.openrouter_api_key is not None and self.settings.enable_llm_nlp

    def extract(self, text: str) -> ShoeQuery:
        if not self.configured():
            raise RuntimeError("OpenRouter NLP is not configured.")
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "brand": {"type": ["string", "null"]},
                "model": {"type": ["string", "null"]},
                "size_us": {"type": ["number", "null"], "minimum": 3, "maximum": 18},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["brand", "model", "size_us", "confidence"],
        }
        payload = {
            "model": self.settings.nlp_model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract a thrift-shoe request into structured fields. Do not invent details. "
                        "Infer Nike for Jordan/Air Force/Dunk only when the model clearly implies it. "
                        "Return null for missing or uncertain fields. Convert only explicitly stated US sizes."
                    ),
                },
                {"role": "user", "content": text},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "shoe_query", "strict": True, "schema": schema},
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
                    json=payload,
                )
                response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Unexpected OpenRouter content type.")
            parsed = json.loads(content)
            return ShoeQuery(
                brand=parsed.get("brand"),
                model=parsed.get("model"),
                size_us=parsed.get("size_us"),
                confidence=parsed.get("confidence", 0.0),
                source="openrouter_nlp",
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LLMProcessingError("LLM text extraction failed.") from exc


class HybridTextParser:
    def __init__(self, settings: Settings) -> None:
        self.rule_parser = RuleTextParser()
        self.llm = OpenRouterTextExtractor(settings)

    @staticmethod
    def merge(primary: ShoeQuery, secondary: ShoeQuery) -> ShoeQuery:
        return ShoeQuery(
            brand=primary.brand or secondary.brand,
            model=primary.model or secondary.model,
            size_us=primary.size_us if primary.size_us is not None else secondary.size_us,
            condition_score=primary.condition_score or secondary.condition_score,
            condition_notes=primary.condition_notes or secondary.condition_notes,
            confidence=max(primary.confidence, secondary.confidence),
            source=f"{primary.source}+{secondary.source}",
        )

    def parse(self, text: str) -> TextParserResult:
        result = self.rule_parser.parse(text)
        if not result.clarification_needed or not self.llm.configured():
            return result
        try:
            llm_query = self.llm.extract(text)
        except LLMProcessingError:
            return result
        query = self.merge(result.query, llm_query)
        missing = missing_fields_for(query)
        return TextParserResult(
            query=query,
            missing_fields=missing,
            clarification_needed=bool(missing),
            clarification_question=build_clarification(missing) if missing else None,
            used_llm=True,
        )

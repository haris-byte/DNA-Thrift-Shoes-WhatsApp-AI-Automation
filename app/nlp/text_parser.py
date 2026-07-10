import re
from app.models.shoe_models import ShoeQuery, TextParserResult


BRAND_KEYWORDS = {
    "nike": "Nike",
    "adidas": "Adidas",
    "puma": "Puma",
    "reebok": "Reebok",
    "new balance": "New Balance",
    "vans": "Vans",
    "converse": "Converse",
    "jordan": "Nike",
    "air jordan": "Nike",
    "air force": "Nike",
    "air force 1": "Nike",
    "af1": "Nike",
    "dunk": "Nike",
    "dunk low": "Nike",
}

MODEL_KEYWORDS = {
    "air jordan 1": "Air Jordan 1",
    "jordan 1": "Air Jordan 1",
    "air force 1": "Air Force 1",
    "af1": "Air Force 1",
    "air max": "Air Max",
    "dunk low": "Dunk Low",
    "yeezy": "Yeezy",
    "ultraboost": "Ultraboost",
    "stan smith": "Stan Smith",
    "superstar": "Superstar",
    "old skool": "Old Skool",
    "chuck taylor": "Chuck Taylor",
}


def normalize_text(text: str) -> str:
    return text.lower().strip()


def contains_phrase(text: str, phrase: str) -> bool:
    escaped_phrase = re.escape(phrase.lower())
    pattern = rf"\b{escaped_phrase}\b"
    return re.search(pattern, text) is not None


def extract_brand(text: str) -> str | None:
    normalized = normalize_text(text)

    sorted_keywords = sorted(
        BRAND_KEYWORDS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for keyword, brand in sorted_keywords:
        if contains_phrase(normalized, keyword):
            return brand

    return None


def extract_model(text: str) -> str | None:
    normalized = normalize_text(text)

    sorted_keywords = sorted(
        MODEL_KEYWORDS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for keyword, model in sorted_keywords:
        if contains_phrase(normalized, keyword):
            return model

    return None


def extract_size(text: str) -> float | None:
    normalized = normalize_text(text)

    patterns = [
        r"\bsize\s*(\d{1,2}(?:\.\d)?)\b",
        r"\bus\s*(\d{1,2}(?:\.\d)?)\b",
        r"\buk\s*(\d{1,2}(?:\.\d)?)\b",
        r"\beu\s*(\d{2})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            return float(match.group(1))

    return None


def calculate_confidence(
    brand: str | None,
    model: str | None,
    size_us: float | None
) -> float:
    score = 0.0

    if brand:
        score += 0.3

    if model:
        score += 0.4

    if size_us:
        score += 0.3

    return round(score, 2)


def build_clarification(missing_fields: list[str]) -> str:
    if "model" in missing_fields and "size_us" in missing_fields:
        return "Which shoe model and US size are you looking for?"

    if "model" in missing_fields:
        return "Which shoe model are you looking for?"

    if "size_us" in missing_fields:
        return "What US size are you looking for?"

    if "brand" in missing_fields:
        return "Which brand are you looking for?"

    return "Can you share the shoe brand, model, and US size?"


def parse_text_query(text: str) -> TextParserResult:
    brand = extract_brand(text)
    model = extract_model(text)
    size_us = extract_size(text)

    missing_fields: list[str] = []

    if not brand:
        missing_fields.append("brand")

    if not model:
        missing_fields.append("model")

    if not size_us:
        missing_fields.append("size_us")

    confidence = calculate_confidence(brand, model, size_us)

    shoe_query = ShoeQuery(
        brand=brand,
        model=model,
        size_us=size_us,
        condition_score=None,
        confidence=confidence,
        source="text_rule_parser"
    )

    clarification_needed = len(missing_fields) > 0

    clarification_question = None
    if clarification_needed:
        clarification_question = build_clarification(missing_fields)

    return TextParserResult(
        query=shoe_query,
        missing_fields=missing_fields,
        clarification_needed=clarification_needed,
        clarification_question=clarification_question
    )
import io
import re
from typing import Optional

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

from app.core.config import Settings
from app.core.errors import ConfigurationError, OCRProcessingError
from app.models.shoe_models import DetectedSize, OCRDetection, OCRResult, SizeSystem
from app.vision.image_io import ImageAsset


EU_TO_US_MENS: dict[float, float] = {
    36: 4, 37: 5, 38: 6, 39: 6.5, 40: 7, 41: 8, 42: 8.5,
    43: 9.5, 44: 10, 45: 11, 46: 12, 47: 13, 48: 14,
}


def _convert_to_us(system: SizeSystem, value: float) -> tuple[Optional[float], bool]:
    if system == SizeSystem.US:
        return value, False
    if system == SizeSystem.UK:
        estimate = value + 1.0
        return (estimate if 3 <= estimate <= 18 else None), True
    if system == SizeSystem.EU:
        return EU_TO_US_MENS.get(value), True
    return None, True


def extract_size_candidates(raw_text: str, confidence: float = 0.75) -> list[DetectedSize]:
    normalized = re.sub(r"\s+", " ", raw_text.upper())
    patterns: list[tuple[SizeSystem, str]] = [
        (SizeSystem.US, r"\b(?:US|USA|US M|MENS US)\s*[:#-]?\s*(\d{1,2}(?:\.5)?)\b"),
        (SizeSystem.UK, r"\bUK\s*[:#-]?\s*(\d{1,2}(?:\.5)?)\b"),
        (SizeSystem.EU, r"\b(?:EU|EUR)\s*[:#-]?\s*(\d{2}(?:\.5)?)\b"),
    ]
    candidates: list[DetectedSize] = []
    seen: set[tuple[SizeSystem, float]] = set()
    for system, pattern in patterns:
        for match in re.finditer(pattern, normalized):
            value = float(match.group(1))
            key = (system, value)
            if key in seen:
                continue
            seen.add(key)
            us_estimate, requires_confirmation = _convert_to_us(system, value)
            candidates.append(
                DetectedSize(
                    system=system,
                    value=value,
                    us_estimate=us_estimate,
                    confidence=confidence,
                    requires_confirmation=requires_confirmation,
                    source_text=match.group(0),
                )
            )
    return candidates


def choose_size(candidates: list[DetectedSize]) -> Optional[DetectedSize]:
    if not candidates:
        return None
    explicit_us = [item for item in candidates if item.system == SizeSystem.US and item.us_estimate is not None]
    pool = explicit_us or [item for item in candidates if item.us_estimate is not None] or candidates
    return sorted(pool, key=lambda item: (item.requires_confirmation, -item.confidence))[0]


class EasyOCRService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._reader: object | None = None

    def _get_reader(self) -> object:
        if not self.settings.enable_easyocr:
            raise ConfigurationError("EasyOCR is disabled in configuration.")
        if self._reader is not None:
            return self._reader
        try:
            import easyocr
            self._reader = easyocr.Reader(["en"], gpu=self.settings.easyocr_gpu)
            return self._reader
        except ImportError as exc:
            raise ConfigurationError(
                "EasyOCR is not installed. Run: pip install -r requirements.txt"
            ) from exc
        except Exception as exc:
            raise OCRProcessingError("EasyOCR could not be initialized.") from exc

    @staticmethod
    def _variants(asset: ImageAsset) -> list[bytes]:
        with Image.open(io.BytesIO(asset.data)) as original:
            rgb = original.convert("RGB")
            variants = [rgb]
            gray = ImageOps.grayscale(rgb)
            gray = ImageOps.autocontrast(gray)
            gray = ImageEnhance.Contrast(gray).enhance(1.8)
            gray = gray.filter(ImageFilter.SHARPEN)
            upscale = gray.resize((gray.width * 2, gray.height * 2))
            variants.extend([gray.convert("RGB"), upscale.convert("RGB")])
            output: list[bytes] = []
            for image in variants:
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                output.append(buffer.getvalue())
            return output

    def analyze(self, asset: ImageAsset) -> OCRResult:
        reader = self._get_reader()
        readtext = getattr(reader, "readtext", None)
        if not callable(readtext):
            raise OCRProcessingError("EasyOCR reader does not expose readtext().")
        detections: list[OCRDetection] = []
        seen_text: set[str] = set()
        try:
            for variant in self._variants(asset):
                raw_results = readtext(
                    variant,
                    detail=1,
                    paragraph=False,
                    rotation_info=[90, 180, 270],
                    allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./:- ",
                )
                for item in raw_results:
                    if not isinstance(item, (list, tuple)) or len(item) < 3:
                        continue
                    text = str(item[1]).strip()
                    try:
                        confidence = float(item[2])
                    except (TypeError, ValueError):
                        continue
                    if text and text not in seen_text:
                        seen_text.add(text)
                        detections.append(OCRDetection(text=text, confidence=max(0.0, min(1.0, confidence))))
        except Exception as exc:
            raise OCRProcessingError("EasyOCR failed while reading the image.") from exc
        raw_text = " ".join(item.text for item in detections)
        average_confidence = (
            sum(item.confidence for item in detections) / len(detections) if detections else 0.0
        )
        candidates = extract_size_candidates(raw_text, confidence=average_confidence)
        selected = choose_size(candidates)
        return OCRResult(
            raw_text=raw_text,
            detections=detections,
            size_candidates=candidates,
            selected_size=selected,
            readable=selected is not None,
        )

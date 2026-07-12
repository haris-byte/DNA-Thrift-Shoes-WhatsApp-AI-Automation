from app.models.shoe_models import PhotoAnalysisResult, ShoeQuery, SizeSystem
from app.vision.image_io import ImageLoader
from app.vision.ocr import EasyOCRService, extract_size_candidates, choose_size
from app.vision.vlm import OpenRouterVisionAnalyzer


class PhotoPipeline:
    def __init__(
        self,
        image_loader: ImageLoader,
        vision_analyzer: OpenRouterVisionAnalyzer,
        ocr_service: EasyOCRService,
    ) -> None:
        self.image_loader = image_loader
        self.vision_analyzer = vision_analyzer
        self.ocr_service = ocr_service

    @staticmethod
    def _clarification(
        brand_missing: bool,
        model_missing: bool,
        size_missing: bool,
        detected_non_us: str | None,
    ) -> str | None:
        if model_missing:
            return (
                "I could not identify the exact shoe model confidently from this photo. "
                "Please send a clearer side/logo photo or type the exact model name."
            )
        if brand_missing:
            return "I could not identify the shoe brand confidently. Please type the brand or send a clearer logo photo."
        if detected_non_us:
            return (
                f"I detected {detected_non_us} on the tag, but size conversion varies by brand and gender. "
                "Please confirm the US size."
            )
        if size_missing:
            return (
                "I identified the shoe, but the size tag was not readable. "
                "Please send a close, sharp tag photo or reply with the US size."
            )
        return None

    def analyze(self, image_source: str) -> PhotoAnalysisResult:
        asset = self.image_loader.load(image_source)
        vision = self.vision_analyzer.analyze(asset)
        ocr = self.ocr_service.analyze(asset)

        if not ocr.readable and vision.visible_size_text:
            fallback_candidates = extract_size_candidates(vision.visible_size_text, confidence=0.45)
            fallback_selected = choose_size(fallback_candidates)
            if fallback_selected is not None:
                ocr = ocr.model_copy(
                    update={
                        "raw_text": (ocr.raw_text + " " + vision.visible_size_text).strip(),
                        "size_candidates": ocr.size_candidates + fallback_candidates,
                        "selected_size": fallback_selected,
                        "readable": True,
                    }
                )

        selected = ocr.selected_size
        explicit_us = (
            selected is not None
            and selected.system == SizeSystem.US
            and not selected.requires_confirmation
        )
        size_us = selected.us_estimate if explicit_us else None

        query = ShoeQuery(
            brand=vision.brand,
            model=vision.model,
            size_us=size_us,
            condition_score=vision.condition_score,
            condition_notes=vision.condition_notes,
            confidence=vision.confidence,
            source="openrouter_vision+easyocr",
        )

        missing_fields: list[str] = []
        if query.brand is None:
            missing_fields.append("brand")
        if query.model is None:
            missing_fields.append("model")
        if query.size_us is None:
            missing_fields.append("size_us")

        detected_non_us = None
        if selected is not None and selected.system != SizeSystem.US:
            detected_non_us = f"{selected.system.value} {selected.value:g}"

        clarification = self._clarification(
            brand_missing=query.brand is None,
            model_missing=query.model is None,
            size_missing=query.size_us is None,
            detected_non_us=detected_non_us,
        )

        return PhotoAnalysisResult(
            vision=vision,
            ocr=ocr,
            query=query,
            missing_fields=missing_fields,
            clarification_needed=bool(missing_fields),
            clarification_question=clarification,
        )

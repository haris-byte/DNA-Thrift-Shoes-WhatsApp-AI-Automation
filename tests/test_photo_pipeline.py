from pathlib import Path

from PIL import Image

from app.models.shoe_models import (
    DetectedSize,
    OCRResult,
    SizeSystem,
    VisionAnalysisResult,
)
from app.vision.image_io import ImageLoader
from app.vision.photo_pipeline import PhotoPipeline


class FakeVision:
    def analyze(self, asset):
        return VisionAnalysisResult(
            brand="Nike",
            model="Air Force 1",
            style_family="low-top sneaker",
            condition_score=7,
            condition_notes=["visible toe-box creasing"],
            confidence=0.88,
            provider_model="fake-test-model",
        )


class FakeUSOCR:
    def analyze(self, asset):
        size = DetectedSize(
            system=SizeSystem.US,
            value=10,
            us_estimate=10,
            confidence=0.9,
            requires_confirmation=False,
            source_text="US 10",
        )
        return OCRResult(
            raw_text="US 10",
            size_candidates=[size],
            selected_size=size,
            readable=True,
        )


class FakeEUOCR:
    def analyze(self, asset):
        size = DetectedSize(
            system=SizeSystem.EU,
            value=44,
            us_estimate=10,
            confidence=0.9,
            requires_confirmation=True,
            source_text="EU 44",
        )
        return OCRResult(
            raw_text="EU 44",
            size_candidates=[size],
            selected_size=size,
            readable=True,
        )


def make_image(path: Path) -> None:
    Image.new("RGB", (100, 100), "white").save(path)


def test_photo_pipeline_builds_complete_query(settings, tmp_path: Path) -> None:
    image_path = tmp_path / "shoe.png"
    make_image(image_path)
    pipeline = PhotoPipeline(ImageLoader(settings), FakeVision(), FakeUSOCR())
    result = pipeline.analyze(str(image_path))
    assert result.clarification_needed is False
    assert result.query.brand == "Nike"
    assert result.query.model == "Air Force 1"
    assert result.query.size_us == 10
    assert result.query.condition_score == 7


def test_non_us_size_requires_confirmation(settings, tmp_path: Path) -> None:
    image_path = tmp_path / "shoe.png"
    make_image(image_path)
    pipeline = PhotoPipeline(ImageLoader(settings), FakeVision(), FakeEUOCR())
    result = pipeline.analyze(str(image_path))
    assert result.clarification_needed is True
    assert result.query.size_us is None
    assert "EU 44" in (result.clarification_question or "")

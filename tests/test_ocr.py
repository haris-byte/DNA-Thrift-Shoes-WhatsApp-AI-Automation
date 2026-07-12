from app.models.shoe_models import SizeSystem
from app.vision.ocr import choose_size, extract_size_candidates


def test_us_size_is_preferred() -> None:
    candidates = extract_size_candidates("US 10 UK 9 EU 44", confidence=0.9)
    selected = choose_size(candidates)
    assert selected is not None
    assert selected.system == SizeSystem.US
    assert selected.us_estimate == 10
    assert selected.requires_confirmation is False


def test_eu_size_requires_confirmation() -> None:
    candidates = extract_size_candidates("EUR 44", confidence=0.8)
    selected = choose_size(candidates)
    assert selected is not None
    assert selected.system == SizeSystem.EU
    assert selected.us_estimate == 10
    assert selected.requires_confirmation is True

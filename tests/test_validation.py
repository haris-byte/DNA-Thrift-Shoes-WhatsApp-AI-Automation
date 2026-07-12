import pytest
from pydantic import ValidationError

from app.models.inventory_models import InventoryMatchResult, MatchType
from app.models.shoe_models import OCRResult, ShoeQuery
from app.models.webhook_models import DevWebhookPayload


def test_unknown_webhook_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DevWebhookPayload.model_validate(
            {
                "sender_id": "user_1",
                "message_id": "msg_1",
                "message_type": "text",
                "text": "Jordan 1 size 10",
                "unexpected": "bad",
            }
        )


def test_blank_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DevWebhookPayload(
            sender_id="user_1",
            message_id="msg_1",
            message_type="text",
            text="   ",
        )


def test_ocr_consistency_is_enforced() -> None:
    with pytest.raises(ValidationError):
        OCRResult(raw_text="US 10", readable=True)


def test_exact_match_requires_item_and_price() -> None:
    with pytest.raises(ValidationError):
        InventoryMatchResult(
            match_type=MatchType.EXACT,
            query=ShoeQuery(brand="Nike", model="Air Force 1", size_us=10, source="test"),
            message="Invalid exact match",
        )


def test_private_image_url_is_rejected(settings) -> None:
    from app.core.errors import ImageDownloadError
    from app.vision.image_io import ImageLoader

    with pytest.raises(ImageDownloadError):
        ImageLoader(settings).load("http://127.0.0.1/private.jpg")

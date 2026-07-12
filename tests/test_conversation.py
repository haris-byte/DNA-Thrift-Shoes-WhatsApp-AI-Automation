from app.conversation.engine import ConversationEngine
from app.inventory.database import (
    IdempotencyRepository,
    InventoryRepository,
    SQLiteDatabase,
    SessionRepository,
)
from app.inventory.service import InventoryService
from app.models.webhook_models import IncomingMessage, MessageType
from app.nlp.text_parser import HybridTextParser


class UnusedPhotoPipeline:
    def analyze(self, image_source: str):  # pragma: no cover - not used in text tests
        raise AssertionError("Photo pipeline should not be used")


def build_engine(settings) -> ConversationEngine:
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    return ConversationEngine(
        settings=settings,
        sessions=SessionRepository(database),
        idempotency=IdempotencyRepository(database),
        text_parser=HybridTextParser(settings),
        photo_pipeline=UnusedPhotoPipeline(),
        inventory=InventoryService(InventoryRepository(database)),
    )


def msg(sender: str, message_id: str, text: str) -> IncomingMessage:
    return IncomingMessage(
        sender_id=sender,
        message_id=message_id,
        message_type=MessageType.TEXT,
        text=text,
    )


def test_multiturn_size_confirmation(settings) -> None:
    engine = build_engine(settings)
    first = engine.handle(msg("u1", "m1", "Air Force 1"))
    assert first.state.value == "AWAITING_SIZE_CONFIRMATION"

    second = engine.handle(msg("u1", "m2", "US 10"))
    assert second.state.value == "AWAITING_PURCHASE_INTENT"
    assert "Air Force 1 White" in second.reply
    assert "9,450" in second.reply


def test_loop_prevention_after_two_failed_followups(settings) -> None:
    engine = build_engine(settings)
    first = engine.handle(msg("loop", "l1", "Nike shoes?"))
    second = engine.handle(msg("loop", "l2", "Nike shoes?"))
    third = engine.handle(msg("loop", "l3", "Nike shoes?"))
    assert first.state.value == "IDENTIFYING_SHOE"
    assert second.state.value == "IDENTIFYING_SHOE"
    assert third.state.value == "FALLBACK_HUMAN"


def test_duplicate_message_is_idempotent(settings) -> None:
    engine = build_engine(settings)
    first = engine.handle(msg("dup", "same-id", "Jordan 1 size 10"))
    second = engine.handle(msg("dup", "same-id", "Nike shoes?"))
    assert first.reply == second.reply
    assert first.state == second.state
    assert first.duplicate_delivery is False
    assert second.duplicate_delivery is True

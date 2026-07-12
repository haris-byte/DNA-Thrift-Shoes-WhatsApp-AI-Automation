from dataclasses import dataclass

from app.conversation.engine import ConversationEngine
from app.core.config import Settings, get_settings
from app.inventory.database import (
    IdempotencyRepository,
    InventoryRepository,
    SQLiteDatabase,
    SessionRepository,
)
from app.inventory.service import InventoryService
from app.nlp.text_parser import HybridTextParser
from app.vision.image_io import ImageLoader
from app.vision.ocr import EasyOCRService
from app.vision.photo_pipeline import PhotoPipeline
from app.vision.vlm import OpenRouterVisionAnalyzer
from app.webhook.meta_client import MetaWhatsAppClient


@dataclass
class AppContainer:
    settings: Settings
    database: SQLiteDatabase
    engine: ConversationEngine
    meta_client: MetaWhatsAppClient


def build_container(settings: Settings | None = None) -> AppContainer:
    settings = settings or get_settings()
    database = SQLiteDatabase(settings.database_path)
    database.initialize()

    inventory_repository = InventoryRepository(database)
    sessions = SessionRepository(database)
    idempotency = IdempotencyRepository(database)
    inventory = InventoryService(inventory_repository)
    text_parser = HybridTextParser(settings)
    photo_pipeline = PhotoPipeline(
        image_loader=ImageLoader(settings),
        vision_analyzer=OpenRouterVisionAnalyzer(settings),
        ocr_service=EasyOCRService(settings),
    )
    engine = ConversationEngine(
        settings=settings,
        sessions=sessions,
        idempotency=idempotency,
        text_parser=text_parser,
        photo_pipeline=photo_pipeline,
        inventory=inventory,
    )
    return AppContainer(
        settings=settings,
        database=database,
        engine=engine,
        meta_client=MetaWhatsAppClient(settings),
    )

from fastapi import FastAPI

from app.container import build_container
from app.core.config import Settings, get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging
from app.models.api_models import HealthResponse
from app.webhook.dev_routes import router as dev_router
from app.webhook.routes import router as whatsapp_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A typed multimodal WhatsApp backend for DNA Thrift. It uses a real "
            "vision-language model for shoe recognition, EasyOCR for size tags, "
            "SQLite inventory/session persistence, and deterministic conversation flow."
        ),
    )
    app.state.container = build_container(settings)
    register_exception_handlers(app)
    app.include_router(dev_router)
    app.include_router(whatsapp_router)

    @app.get("/", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        return HealthResponse(
            application=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )

    return app


app = create_app()

from app.container import build_container
from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    container = build_container(settings)
    print(f"Application: {settings.app_name} {settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Database: {container.database.path} (initialized)")
    print(f"OpenRouter configured: {settings.vision_is_configured}")
    print(f"WhatsApp sending configured: {settings.whatsapp_is_configured}")
    try:
        import easyocr  # noqa: F401
        print("EasyOCR installed: True")
    except ImportError:
        print("EasyOCR installed: False")


if __name__ == "__main__":
    main()

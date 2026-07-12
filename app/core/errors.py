class AppError(Exception):
    def __init__(self, *, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class ConfigurationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="configuration_error", message=message, status_code=503)


class ImageDownloadError(AppError):
    def __init__(self, message: str = "The image could not be downloaded.") -> None:
        super().__init__(code="image_download_failed", message=message, status_code=422)


class UnsupportedImageError(AppError):
    def __init__(self, message: str = "Unsupported or corrupted image.") -> None:
        super().__init__(code="unsupported_image", message=message, status_code=415)


class OCRProcessingError(AppError):
    def __init__(self, message: str = "OCR processing failed.") -> None:
        super().__init__(code="ocr_processing_failed", message=message, status_code=422)


class LLMProcessingError(AppError):
    def __init__(self, message: str = "Language-model processing failed.") -> None:
        super().__init__(code="llm_processing_failed", message=message, status_code=422)


class VisionProcessingError(AppError):
    def __init__(self, message: str = "Vision analysis failed.") -> None:
        super().__init__(code="vision_processing_failed", message=message, status_code=422)


class InventoryProcessingError(AppError):
    def __init__(self, message: str = "Inventory lookup failed.") -> None:
        super().__init__(code="inventory_processing_failed", message=message, status_code=500)


class WhatsAppProcessingError(AppError):
    def __init__(self, message: str = "WhatsApp processing failed.") -> None:
        super().__init__(code="whatsapp_processing_failed", message=message, status_code=502)

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.models.error_models import ErrorBody, ErrorDetail, ErrorResponse


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(part) for part in error.get("loc", [])) or None,
                message=str(error.get("msg", "Invalid input.")),
                error_type=str(error.get("type", "validation_error")),
            )
            for error in exc.errors()
        ]
        logger.warning("request_validation_failed path=%s count=%s", request.url.path, len(details))
        response = ErrorResponse(
            error=ErrorBody(
                code="request_validation_failed",
                message="The incoming request is malformed or incomplete.",
                details=details,
            )
        )
        return JSONResponse(status_code=422, content=response.model_dump(mode="json"))

    @app.exception_handler(AppError)
    async def application_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "application_error path=%s code=%s message=%s",
            request.url.path,
            exc.code,
            exc.message,
        )
        response = ErrorResponse(error=ErrorBody(code=exc.code, message=exc.message))
        return JSONResponse(status_code=exc.status_code, content=response.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected_error path=%s", request.url.path)
        response = ErrorResponse(
            error=ErrorBody(
                code="internal_server_error",
                message="An unexpected internal error occurred. The failure has been logged.",
            )
        )
        return JSONResponse(status_code=500, content=response.model_dump(mode="json"))

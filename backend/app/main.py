"""FastAPI application for the onboarding readiness auditor."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.exceptions import (
    AuditorError,
    CatalogValidationError,
    FileValidationError,
    LLMParsingError,
    PDFExtractionError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

_ERROR_STATUS_CODES: dict[type[Exception], int] = {
    FileValidationError: 400,
    PDFExtractionError: 422,
    CatalogValidationError: 422,
    LLMParsingError: 502,
}


def _status_for_error(exc: AuditorError) -> int:
    """Resolve the HTTP status for a domain error via its most specific class."""
    for cls in type(exc).__mro__:
        if cls in _ERROR_STATUS_CODES:
            return _ERROR_STATUS_CODES[cls]
    return 500


def register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to consistent JSON error responses."""

    @app.exception_handler(AuditorError)
    async def handle_auditor_error(request: Request, exc: AuditorError) -> JSONResponse:
        status = _status_for_error(exc)
        logger.warning("request to %s failed: %s", request.url.path, exc)
        return JSONResponse(status_code=status, content={"detail": str(exc)})


def create_app() -> FastAPI:
    """Build the FastAPI application with CORS and the API router mounted."""
    app = FastAPI(title="Comena Onboarding Readiness Auditor", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(router)
    return app


app = create_app()

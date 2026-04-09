from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.exception_handlers import register_exception_handlers
from app.api.routes import router as api_router
from app.config import get_settings
from app.schemas.response import ErrorResponse
from app.utils.logger import configure_logging, get_logger


logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        description="Multi-tool agent office assistant service skeleton.",
    )
    register_exception_handlers(application)

    @application.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore[no-untyped-def]
        start_time = perf_counter()
        logger.info("Request started: %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    status="error",
                    message="Internal server error.",
                    error_code="internal_server_error",
                    details={},
                ).model_dump(),
            )
        duration_ms = (perf_counter() - start_time) * 1000
        logger.info(
            "Request completed: %s %s -> %s in %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    application.include_router(api_router, prefix=settings.api_prefix)

    @application.get("/", tags=["meta"])
    def read_root() -> dict[str, str]:
        return {"message": f"{settings.app_name} is running"}

    return application


app = create_app()

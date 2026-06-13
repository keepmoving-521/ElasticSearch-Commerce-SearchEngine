from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI

from commerce_search.api.router import api_router
from commerce_search.shared.config import get_settings
from commerce_search.shared.logging import configure_logging
from commerce_search.shared.middleware import RequestContextMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = structlog.get_logger(__name__)
    await logger.ainfo("application_started", environment=settings.environment)
    yield
    await logger.ainfo("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()

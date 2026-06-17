from fastapi import FastAPI

from commerce_search.api.exception_handlers import register_exception_handlers
from commerce_search.api.router import api_router
from commerce_search.bootstrap.lifecycle import (
    ContainerFactory,
    create_lifespan,
)
from commerce_search.shared.config import Settings, get_settings
from commerce_search.shared.middleware import RequestContextMiddleware


def create_app(
    settings: Settings | None = None,
    *,
    container_factory: ContainerFactory | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    lifespan = (
        create_lifespan(
            resolved_settings,
            container_factory=container_factory,
        )
        if container_factory is not None
        else create_lifespan(resolved_settings)
    )
    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        debug=resolved_settings.debug,
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.docs_enabled else None,
        lifespan=lifespan,
    )
    app.add_middleware(
        RequestContextMiddleware,
        access_log_enabled=resolved_settings.access_log_enabled,
        request_id_max_length=resolved_settings.request_id_max_length,
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=resolved_settings.api_prefix)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "commerce_search.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )

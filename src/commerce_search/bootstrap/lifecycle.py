from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import structlog
from fastapi import FastAPI

from commerce_search.bootstrap.container import ApplicationContainer
from commerce_search.shared.config import Settings
from commerce_search.shared.logging import configure_logging

ContainerFactory = Callable[[Settings], ApplicationContainer]


def create_lifespan(
    settings: Settings,
    *,
    container_factory: ContainerFactory = ApplicationContainer.from_settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.log_level)
        logger = structlog.get_logger(__name__)
        container = container_factory(settings)
        app.state.container = container
        lifecycle_error: BaseException | None = None

        try:
            await container.start()
            await logger.ainfo(
                "application_started",
                environment=settings.environment,
            )
            yield
        except BaseException as exc:
            lifecycle_error = exc
            await logger.aexception("application_lifecycle_failed")
        shutdown_error: BaseException | None = None
        try:
            await container.close()
        except BaseException as exc:
            shutdown_error = exc
            await logger.aexception("application_shutdown_failed")
        finally:
            await logger.ainfo("application_stopped")

        if lifecycle_error is not None and shutdown_error is not None:
            raise BaseExceptionGroup(
                "Application lifecycle and shutdown both failed",
                [lifecycle_error, shutdown_error],
            )
        if lifecycle_error is not None:
            raise lifecycle_error
        if shutdown_error is not None:
            raise shutdown_error

    return lifespan

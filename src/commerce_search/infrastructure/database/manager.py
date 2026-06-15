from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from commerce_search.shared.config import Settings


class DatabaseManager:
    def __init__(
        self,
        database_url: str | URL,
        *,
        echo: bool = False,
        pool_size: int | None = None,
        max_overflow: int | None = None,
        pool_timeout: int | None = None,
        pool_recycle: int | None = None,
    ) -> None:
        self.database_url = database_url
        self._engine_options: dict[str, Any] = {
            "echo": echo,
            "pool_pre_ping": True,
        }
        if pool_size is not None:
            self._engine_options["pool_size"] = pool_size
        if max_overflow is not None:
            self._engine_options["max_overflow"] = max_overflow
        if pool_timeout is not None:
            self._engine_options["pool_timeout"] = pool_timeout
        if pool_recycle is not None:
            self._engine_options["pool_recycle"] = pool_recycle

        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "DatabaseManager":
        database_url = URL.create(
            drivername="postgresql+asyncpg",
            username=settings.postgres_user,
            password=settings.postgres_password.get_secret_value(),
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
        )
        return cls(
            database_url,
            echo=settings.postgres_echo,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_timeout=settings.postgres_pool_timeout,
            pool_recycle=settings.postgres_pool_recycle,
        )

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self.database_url,
                **self._engine_options,
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory

    def session(self) -> AsyncSession:
        return self.session_factory()

    @asynccontextmanager
    async def session_context(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    async def ping(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

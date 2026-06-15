from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from commerce_search.infrastructure.database.manager import DatabaseManager


def get_database_manager(request: Request) -> DatabaseManager:
    database: DatabaseManager = request.app.state.database
    return database


async def get_db_session(
    database: Annotated[DatabaseManager, Depends(get_database_manager)],
) -> AsyncIterator[AsyncSession]:
    async with database.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from commerce_search.infrastructure.database.manager import DatabaseManager
from commerce_search.infrastructure.dependencies import get_database_manager


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

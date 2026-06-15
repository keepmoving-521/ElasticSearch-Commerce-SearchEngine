from typing import Any, cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from commerce_search.infrastructure.database.uow import SqlAlchemyUnitOfWork


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.closed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def close(self) -> None:
        self.closed = True


def session_factory(session: FakeSession) -> async_sessionmaker[AsyncSession]:
    def factory() -> AsyncSession:
        return cast(AsyncSession, session)

    return cast(async_sessionmaker[AsyncSession], cast(Any, factory))


async def test_unit_of_work_commits_and_closes_on_success() -> None:
    session = FakeSession()
    typed_session = cast(AsyncSession, session)

    async with SqlAlchemyUnitOfWork(session_factory(session)) as unit_of_work:
        assert unit_of_work.session is typed_session

    assert session.committed is True
    assert session.rolled_back is False
    assert session.closed is True


async def test_unit_of_work_rolls_back_and_closes_on_error() -> None:
    session = FakeSession()

    with pytest.raises(RuntimeError, match="write failed"):
        async with SqlAlchemyUnitOfWork(session_factory(session)):
            raise RuntimeError("write failed")

    assert session.committed is False
    assert session.rolled_back is True
    assert session.closed is True

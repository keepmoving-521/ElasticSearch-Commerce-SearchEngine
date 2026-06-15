from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from commerce_search.bootstrap.container import ApplicationContainer
from commerce_search.main import create_app
from commerce_search.shared.config import Environment, Settings


class FakeContainer:
    def __init__(self, *, fail_start: bool = False) -> None:
        self.fail_start = fail_start
        self.started = False
        self.closed = False

    async def start(self) -> None:
        self.started = True
        if self.fail_start:
            raise RuntimeError("startup failed")

    async def close(self) -> None:
        self.closed = True


def test_lifecycle_starts_and_closes_injected_container() -> None:
    container = FakeContainer()
    settings = Settings(_env_file=None, environment=Environment.TEST)
    app = create_app(
        settings,
        container_factory=lambda _: cast(ApplicationContainer, cast(Any, container)),
    )

    with TestClient(app):
        assert container.started is True
        assert container.closed is False

    assert container.closed is True


def test_lifecycle_cleans_up_after_startup_failure() -> None:
    container = FakeContainer(fail_start=True)
    settings = Settings(_env_file=None, environment=Environment.TEST)
    app = create_app(
        settings,
        container_factory=lambda _: cast(ApplicationContainer, cast(Any, container)),
    )

    with (
        pytest.raises(RuntimeError, match="startup failed"),
        TestClient(app),
    ):
        pass

    assert container.closed is True

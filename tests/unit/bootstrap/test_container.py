from typing import Any, cast

import pytest

from commerce_search.bootstrap.container import (
    ApplicationContainer,
    ContainerState,
)
from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.shared.config import Environment, Settings


class FakeInfrastructure:
    def __init__(self) -> None:
        self.close_count = 0

    async def close(self) -> None:
        self.close_count += 1


def assert_state(
    container: ApplicationContainer,
    expected: ContainerState,
) -> None:
    assert container.state == expected


async def test_container_tracks_state_and_closes_once() -> None:
    infrastructure = FakeInfrastructure()
    container = ApplicationContainer(
        settings=Settings(_env_file=None, environment=Environment.TEST),
        infrastructure=cast(InfrastructureClients, infrastructure),
    )

    assert_state(container, ContainerState.CREATED)

    await container.start()
    await container.close()
    await container.close()

    assert_state(container, ContainerState.STOPPED)
    assert infrastructure.close_count == 1


async def test_stopped_container_cannot_restart() -> None:
    infrastructure = FakeInfrastructure()
    container = ApplicationContainer(
        settings=Settings(_env_file=None, environment=Environment.TEST),
        infrastructure=cast(InfrastructureClients, cast(Any, infrastructure)),
    )
    await container.close()

    with pytest.raises(RuntimeError, match="cannot be restarted"):
        await container.start()

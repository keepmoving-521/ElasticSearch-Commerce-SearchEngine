from enum import StrEnum

from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.infrastructure.database import SqlAlchemyUnitOfWork
from commerce_search.shared.config import Settings


class ContainerState(StrEnum):
    CREATED = "created"
    STARTED = "started"
    STOPPED = "stopped"


class ApplicationContainer:
    def __init__(
        self,
        *,
        settings: Settings,
        infrastructure: InfrastructureClients,
    ) -> None:
        self.settings = settings
        self.infrastructure = infrastructure
        self.state = ContainerState.CREATED

    @classmethod
    def from_settings(cls, settings: Settings) -> "ApplicationContainer":
        return cls(
            settings=settings,
            infrastructure=InfrastructureClients.from_settings(settings),
        )

    async def start(self) -> None:
        if self.state == ContainerState.STOPPED:
            raise RuntimeError("A stopped application container cannot be restarted")
        self.state = ContainerState.STARTED

    def new_unit_of_work(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(
            self.infrastructure.database.session_factory,
        )

    async def close(self) -> None:
        if self.state == ContainerState.STOPPED:
            return
        try:
            await self.infrastructure.close()
        finally:
            self.state = ContainerState.STOPPED

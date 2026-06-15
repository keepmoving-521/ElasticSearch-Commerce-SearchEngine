from typing import Annotated

from fastapi import Depends, Request

from commerce_search.bootstrap.container import ApplicationContainer
from commerce_search.infrastructure.cache import RedisManager
from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.infrastructure.database import (
    DatabaseManager,
    SqlAlchemyUnitOfWork,
)
from commerce_search.infrastructure.messaging import KafkaProducerManager
from commerce_search.infrastructure.search import ElasticsearchManager
from commerce_search.shared.config import Settings


def get_container(request: Request) -> ApplicationContainer:
    container: ApplicationContainer = request.app.state.container
    return container


def get_app_settings(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> Settings:
    return container.settings


def get_infrastructure_clients(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> InfrastructureClients:
    return container.infrastructure


def get_database_manager(
    clients: Annotated[
        InfrastructureClients,
        Depends(get_infrastructure_clients),
    ],
) -> DatabaseManager:
    return clients.database


def get_elasticsearch_manager(
    clients: Annotated[
        InfrastructureClients,
        Depends(get_infrastructure_clients),
    ],
) -> ElasticsearchManager:
    return clients.elasticsearch


def get_redis_manager(
    clients: Annotated[
        InfrastructureClients,
        Depends(get_infrastructure_clients),
    ],
) -> RedisManager:
    return clients.redis


def get_kafka_producer(
    clients: Annotated[
        InfrastructureClients,
        Depends(get_infrastructure_clients),
    ],
) -> KafkaProducerManager:
    return clients.kafka


def get_unit_of_work(
    container: Annotated[ApplicationContainer, Depends(get_container)],
) -> SqlAlchemyUnitOfWork:
    return container.new_unit_of_work()


ContainerDep = Annotated[ApplicationContainer, Depends(get_container)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
InfrastructureDep = Annotated[
    InfrastructureClients,
    Depends(get_infrastructure_clients),
]
DatabaseManagerDep = Annotated[DatabaseManager, Depends(get_database_manager)]
ElasticsearchDep = Annotated[
    ElasticsearchManager,
    Depends(get_elasticsearch_manager),
]
RedisDep = Annotated[RedisManager, Depends(get_redis_manager)]
KafkaProducerDep = Annotated[
    KafkaProducerManager,
    Depends(get_kafka_producer),
]
UnitOfWorkDep = Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)]

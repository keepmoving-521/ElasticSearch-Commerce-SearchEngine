from typing import Any, cast

from commerce_search.bootstrap.container import ApplicationContainer
from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.infrastructure.dependencies import (
    get_app_settings,
    get_database_manager,
    get_elasticsearch_manager,
    get_infrastructure_clients,
    get_kafka_producer,
    get_redis_manager,
)
from commerce_search.shared.config import Environment, Settings


class FakeClients:
    def __init__(self) -> None:
        self.database = object()
        self.elasticsearch = object()
        self.redis = object()
        self.kafka = object()


def test_dependencies_resolve_resources_from_one_container() -> None:
    settings = Settings(_env_file=None, environment=Environment.TEST)
    clients = FakeClients()
    typed_clients = cast(InfrastructureClients, cast(Any, clients))
    container = ApplicationContainer(
        settings=settings,
        infrastructure=typed_clients,
    )

    resolved_clients = get_infrastructure_clients(container)

    assert get_app_settings(container) is settings
    assert resolved_clients is typed_clients
    assert get_database_manager(resolved_clients) is clients.database
    assert get_elasticsearch_manager(resolved_clients) is clients.elasticsearch
    assert get_redis_manager(resolved_clients) is clients.redis
    assert get_kafka_producer(resolved_clients) is clients.kafka

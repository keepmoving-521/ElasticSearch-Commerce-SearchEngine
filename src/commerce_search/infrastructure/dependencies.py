from fastapi import Request

from commerce_search.infrastructure.cache import RedisManager
from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.infrastructure.messaging import KafkaProducerManager
from commerce_search.infrastructure.search import ElasticsearchManager


def get_infrastructure_clients(request: Request) -> InfrastructureClients:
    clients: InfrastructureClients = request.app.state.infrastructure
    return clients


def get_elasticsearch_manager(request: Request) -> ElasticsearchManager:
    return get_infrastructure_clients(request).elasticsearch


def get_redis_manager(request: Request) -> RedisManager:
    return get_infrastructure_clients(request).redis


def get_kafka_producer(request: Request) -> KafkaProducerManager:
    return get_infrastructure_clients(request).kafka

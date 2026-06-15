import asyncio

from commerce_search.infrastructure.cache import RedisManager
from commerce_search.infrastructure.database import DatabaseManager
from commerce_search.infrastructure.messaging import KafkaProducerManager
from commerce_search.infrastructure.search import ElasticsearchManager
from commerce_search.shared.config import Settings


class InfrastructureClients:
    def __init__(
        self,
        *,
        database: DatabaseManager,
        elasticsearch: ElasticsearchManager,
        redis: RedisManager,
        kafka: KafkaProducerManager,
    ) -> None:
        self.database = database
        self.elasticsearch = elasticsearch
        self.redis = redis
        self.kafka = kafka

    @classmethod
    def from_settings(cls, settings: Settings) -> "InfrastructureClients":
        return cls(
            database=DatabaseManager.from_settings(settings),
            elasticsearch=ElasticsearchManager.from_settings(settings),
            redis=RedisManager.from_settings(settings),
            kafka=KafkaProducerManager.from_settings(settings),
        )

    async def close(self) -> None:
        await asyncio.gather(
            self.database.dispose(),
            self.elasticsearch.close(),
            self.redis.close(),
            self.kafka.close(),
        )

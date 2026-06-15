import asyncio
from collections.abc import Awaitable

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
        operations: dict[str, Awaitable[None]] = {
            "database": self.database.dispose(),
            "elasticsearch": self.elasticsearch.close(),
            "redis": self.redis.close(),
            "kafka": self.kafka.close(),
        }
        results = await asyncio.gather(
            *operations.values(),
            return_exceptions=True,
        )
        cancellation = next(
            (exception for exception in results if isinstance(exception, asyncio.CancelledError)),
            None,
        )
        if cancellation is not None:
            raise cancellation

        failures = [exception for exception in results if isinstance(exception, Exception)]
        if failures:
            raise ExceptionGroup(
                "One or more infrastructure clients failed to close",
                failures,
            )

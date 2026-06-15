import asyncio
import json
from collections.abc import Mapping, Sequence
from typing import Any

from commerce_search.shared.config import Settings


class KafkaProducerManager:
    def __init__(
        self,
        bootstrap_servers: Sequence[str],
        *,
        client_id: str,
        request_timeout_ms: int = 30000,
    ) -> None:
        self.bootstrap_servers = list(bootstrap_servers)
        self.client_id = client_id
        self.request_timeout_ms = request_timeout_ms
        self._producer: Any | None = None
        self._started = False
        self._start_lock = asyncio.Lock()

    @classmethod
    def from_settings(cls, settings: Settings) -> "KafkaProducerManager":
        return cls(
            settings.kafka_servers,
            client_id=settings.kafka_client_id,
            request_timeout_ms=settings.kafka_request_timeout_ms,
        )

    @property
    def producer(self) -> Any:
        if self._producer is None:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                request_timeout_ms=self.request_timeout_ms,
                enable_idempotence=True,
                acks="all",
            )
        return self._producer

    async def start(self) -> None:
        if self._started:
            return
        async with self._start_lock:
            if not self._started:
                await self.producer.start()
                self._started = True

    async def publish_json(
        self,
        topic: str,
        event: Mapping[str, Any],
        *,
        key: str | bytes | None = None,
        headers: Sequence[tuple[str, bytes]] | None = None,
    ) -> Any:
        await self.start()
        encoded_key = key.encode("utf-8") if isinstance(key, str) else key
        payload = json.dumps(
            event,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return await self.producer.send_and_wait(
            topic,
            value=payload,
            key=encoded_key,
            headers=list(headers) if headers else None,
        )

    async def ping(self) -> None:
        await self.start()
        if not self.producer.bootstrap_connected():
            raise ConnectionError("Kafka bootstrap connection failed")

    async def close(self) -> None:
        if self._producer is not None:
            if self._started:
                await self._producer.stop()
            self._producer = None
            self._started = False

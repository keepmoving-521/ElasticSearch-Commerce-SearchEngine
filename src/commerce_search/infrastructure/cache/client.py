import json
from typing import Any

from commerce_search.shared.config import Settings


class RedisManager:
    def __init__(
        self,
        url: str,
        *,
        key_prefix: str,
        max_connections: int = 50,
        socket_timeout: float = 3.0,
    ) -> None:
        self.url = url
        self.key_prefix = key_prefix.strip(":")
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self._client: Any | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "RedisManager":
        return cls(
            settings.redis_url,
            key_prefix=settings.redis_key_prefix,
            max_connections=settings.redis_max_connections,
            socket_timeout=settings.redis_socket_timeout,
        )

    @property
    def client(self) -> Any:
        if self._client is None:
            from redis.asyncio import Redis

            self._client = Redis.from_url(
                self.url,
                decode_responses=True,
                max_connections=self.max_connections,
                socket_connect_timeout=self.socket_timeout,
                socket_timeout=self.socket_timeout,
                health_check_interval=30,
            )
        return self._client

    def key(self, name: str) -> str:
        return f"{self.key_prefix}:{name.lstrip(':')}"

    async def get_json(self, name: str) -> Any | None:
        value = await self.client.get(self.key(name))
        return json.loads(value) if value is not None else None

    async def set_json(
        self,
        name: str,
        value: Any,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        await self.client.set(self.key(name), payload, ex=ttl_seconds)

    async def delete(self, name: str) -> None:
        await self.client.delete(self.key(name))

    async def ping(self) -> None:
        if not await self.client.ping():
            raise ConnectionError("Redis ping failed")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

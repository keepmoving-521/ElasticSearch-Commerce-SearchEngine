import json

from commerce_search.infrastructure.cache import RedisManager


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.closed = False

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ex: int | None,
    ) -> None:
        self.values[key] = value

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        self.closed = True


async def test_redis_manager_namespaces_and_serializes_json() -> None:
    manager = RedisManager(
        "redis://localhost:6379/0",
        key_prefix="commerce:test",
    )
    fake_client = FakeRedis()
    manager._client = fake_client

    await manager.set_json("products:1", {"name": "键盘"}, ttl_seconds=60)

    assert manager.key(":products:1") == "commerce:test:products:1"
    assert json.loads(fake_client.values["commerce:test:products:1"]) == {"name": "键盘"}
    assert await manager.get_json("products:1") == {"name": "键盘"}

    await manager.delete("products:1")
    assert await manager.get_json("products:1") is None


async def test_redis_manager_closes_initialized_client() -> None:
    manager = RedisManager("redis://localhost:6379/0", key_prefix="test")
    fake_client = FakeRedis()
    manager._client = fake_client

    await manager.ping()
    await manager.close()

    assert fake_client.closed is True
    assert manager._client is None

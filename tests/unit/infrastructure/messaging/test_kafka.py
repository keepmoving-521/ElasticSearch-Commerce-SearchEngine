import json
from typing import Any

from commerce_search.infrastructure.messaging import KafkaProducerManager


class FakeProducer:
    def __init__(self) -> None:
        self.start_count = 0
        self.stopped = False
        self.message: dict[str, Any] | None = None

    async def start(self) -> None:
        self.start_count += 1

    def bootstrap_connected(self) -> bool:
        return True

    async def send_and_wait(self, topic: str, **message: Any) -> str:
        self.message = {"topic": topic, **message}
        return "metadata"

    async def stop(self) -> None:
        self.stopped = True


async def test_kafka_manager_starts_once_and_publishes_json() -> None:
    manager = KafkaProducerManager(
        ["localhost:9092"],
        client_id="test-client",
    )
    producer = FakeProducer()
    manager._producer = producer

    result = await manager.publish_json(
        "product.changed",
        {"product_id": "1", "name": "键盘"},
        key="1",
        headers=[("event_type", b"product.changed")],
    )
    await manager.ping()

    assert result == "metadata"
    assert producer.start_count == 1
    assert producer.message is not None
    assert producer.message["topic"] == "product.changed"
    assert producer.message["key"] == b"1"
    assert json.loads(producer.message["value"]) == {
        "product_id": "1",
        "name": "键盘",
    }

    await manager.close()
    assert producer.stopped is True
    assert manager._producer is None

from commerce_search.infrastructure.search import ElasticsearchManager


class FakeElasticsearch:
    def __init__(self, ping_result: bool = True) -> None:
        self.ping_result = ping_result
        self.closed = False

    async def ping(self) -> bool:
        return self.ping_result

    async def close(self) -> None:
        self.closed = True


async def test_elasticsearch_manager_pings_and_closes_client() -> None:
    manager = ElasticsearchManager("http://localhost:9200")
    fake_client = FakeElasticsearch()
    manager._client = fake_client

    await manager.ping()
    await manager.close()

    assert fake_client.closed is True
    assert manager._client is None

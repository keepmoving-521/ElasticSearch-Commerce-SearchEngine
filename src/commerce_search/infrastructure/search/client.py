from typing import Any

from commerce_search.shared.config import Settings


class ElasticsearchManager:
    def __init__(
        self,
        url: str,
        *,
        request_timeout: float = 3.0,
        max_retries: int = 3,
    ) -> None:
        self.url = url
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self._client: Any | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "ElasticsearchManager":
        return cls(
            settings.elasticsearch_url,
            request_timeout=settings.elasticsearch_request_timeout,
            max_retries=settings.elasticsearch_max_retries,
        )

    @property
    def client(self) -> Any:
        if self._client is None:
            from elasticsearch import AsyncElasticsearch

            self._client = AsyncElasticsearch(
                hosts=[self.url],
                request_timeout=self.request_timeout,
                max_retries=self.max_retries,
                retry_on_timeout=True,
            )
        return self._client

    async def ping(self) -> None:
        if not await self.client.ping():
            raise ConnectionError("Elasticsearch ping failed")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

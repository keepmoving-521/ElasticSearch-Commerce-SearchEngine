from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from commerce_search.infrastructure.cache import RedisManager
from commerce_search.infrastructure.database.manager import DatabaseManager
from commerce_search.infrastructure.messaging import KafkaProducerManager
from commerce_search.infrastructure.search import ElasticsearchManager
from commerce_search.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(DatabaseManager, "ping", AsyncMock())
    monkeypatch.setattr(ElasticsearchManager, "ping", AsyncMock())
    monkeypatch.setattr(RedisManager, "ping", AsyncMock())
    monkeypatch.setattr(KafkaProducerManager, "ping", AsyncMock())
    with TestClient(app) as test_client:
        yield test_client

from sqlalchemy import URL

from commerce_search.infrastructure.database.manager import DatabaseManager
from commerce_search.shared.config import Environment, Settings


def test_manager_builds_encoded_postgres_url_without_opening_pool() -> None:
    settings = Settings(
        _env_file=None,
        environment=Environment.DEVELOPMENT,
        postgres_user="search@service",
        postgres_password="p@ss/word",
        postgres_host="database.internal",
        postgres_port=5433,
        postgres_db="products",
    )

    manager = DatabaseManager.from_settings(settings)

    assert isinstance(manager.database_url, URL)
    assert manager.database_url.drivername == "postgresql+asyncpg"
    assert manager.database_url.username == "search@service"
    assert manager.database_url.password == "p@ss/word"
    assert manager.database_url.host == "database.internal"
    assert manager.database_url.port == 5433
    assert manager.database_url.database == "products"
    assert manager._engine is None

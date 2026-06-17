import pytest
from pydantic import ValidationError

from commerce_search.shared.config import (
    Environment,
    Settings,
    get_settings,
)


def production_settings(*, debug: bool = False) -> Settings:
    return Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        debug=debug,
        postgres_host="postgres.internal",
        postgres_password="strong-production-password",
        elasticsearch_url="https://elasticsearch.internal:9200",
        redis_url="rediss://redis.internal:6379/0",
        kafka_bootstrap_servers="kafka.internal:9092",
    )


def test_development_defaults_enable_debug_logging() -> None:
    settings = Settings(_env_file=None, environment=Environment.DEVELOPMENT)

    assert settings.debug is True
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "console"
    assert settings.docs_enabled is True


def test_explicit_development_values_are_preserved() -> None:
    settings = Settings(
        _env_file=None,
        environment=Environment.DEVELOPMENT,
        debug=False,
        log_level="WARNING",
        configured_log_format="json",
    )

    assert settings.debug is False
    assert settings.log_level == "WARNING"
    assert settings.log_format == "json"


def test_local_environment_is_supported_as_legacy_alias() -> None:
    settings = Settings(_env_file=None, environment="local")

    assert settings.environment == Environment.DEVELOPMENT


def test_get_settings_reads_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("POSTGRES_DB", "commerce_search_isolated_test")
    get_settings.cache_clear()

    try:
        settings = get_settings()

        assert settings.environment == Environment.TEST
        assert settings.postgres_db == "commerce_search_isolated_test"
        assert settings.debug is False
        assert settings.is_test is True
    finally:
        get_settings.cache_clear()


def test_production_rejects_unsafe_defaults() -> None:
    with pytest.raises(ValidationError, match="Unsafe production configuration"):
        Settings(_env_file=None, environment=Environment.PRODUCTION)


def test_production_rejects_debug_mode() -> None:
    with pytest.raises(ValidationError, match="APP_DEBUG must be false"):
        production_settings(debug=True)


def test_safe_production_configuration_disables_docs() -> None:
    settings = production_settings()

    assert settings.environment == Environment.PRODUCTION
    assert settings.debug is False
    assert settings.log_format == "json"
    assert settings.docs_enabled is False
    assert str(settings.postgres_password) == "**********"

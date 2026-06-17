from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASE_ENV_FILE = PROJECT_ROOT / ".env"


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


def _normalize_environment(value: Any) -> Any:
    if isinstance(value, str) and value.lower() == "local":
        return Environment.DEVELOPMENT
    return value


class EnvironmentSelector(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        validation_alias="APP_ENV",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: Any) -> Any:
        return _normalize_environment(value)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = Field(default="commerce-search", validation_alias="APP_NAME")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        validation_alias="APP_ENV",
    )
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = Field(default="INFO", validation_alias="APP_LOG_LEVEL")
    configured_log_format: Literal["json", "console"] | None = Field(
        default=None,
        validation_alias="APP_LOG_FORMAT",
    )
    access_log_enabled: bool = Field(
        default=True,
        validation_alias="APP_ACCESS_LOG_ENABLED",
    )
    request_id_max_length: int = Field(
        default=128,
        ge=16,
        le=256,
        validation_alias="APP_REQUEST_ID_MAX_LENGTH",
    )
    health_check_timeout_seconds: float = Field(
        default=2.0,
        gt=0,
        le=30,
        validation_alias="APP_HEALTH_CHECK_TIMEOUT_SECONDS",
    )
    api_prefix: str = Field(default="/api/v1", validation_alias="APP_API_PREFIX")

    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="commerce_search", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="commerce", validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        default=SecretStr("commerce"),
        validation_alias="POSTGRES_PASSWORD",
    )
    postgres_pool_size: int = Field(default=10, validation_alias="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(
        default=20,
        validation_alias="POSTGRES_MAX_OVERFLOW",
    )
    postgres_pool_timeout: int = Field(
        default=30,
        validation_alias="POSTGRES_POOL_TIMEOUT",
    )
    postgres_pool_recycle: int = Field(
        default=1800,
        validation_alias="POSTGRES_POOL_RECYCLE",
    )
    postgres_echo: bool = Field(default=False, validation_alias="POSTGRES_ECHO")

    elasticsearch_url: str = Field(
        default="http://localhost:9200",
        validation_alias="ELASTICSEARCH_URL",
    )
    elasticsearch_request_timeout: float = Field(
        default=3.0,
        validation_alias="ELASTICSEARCH_REQUEST_TIMEOUT",
    )
    elasticsearch_max_retries: int = Field(
        default=3,
        validation_alias="ELASTICSEARCH_MAX_RETRIES",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )
    redis_key_prefix: str = Field(
        default="commerce-search",
        validation_alias="REDIS_KEY_PREFIX",
    )
    redis_max_connections: int = Field(
        default=50,
        validation_alias="REDIS_MAX_CONNECTIONS",
    )
    redis_socket_timeout: float = Field(
        default=3.0,
        validation_alias="REDIS_SOCKET_TIMEOUT",
    )
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias="KAFKA_BOOTSTRAP_SERVERS",
    )
    kafka_client_id: str = Field(
        default="commerce-search",
        validation_alias="KAFKA_CLIENT_ID",
    )
    kafka_request_timeout_ms: int = Field(
        default=30000,
        validation_alias="KAFKA_REQUEST_TIMEOUT_MS",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: Any) -> Any:
        return _normalize_environment(value)

    @model_validator(mode="after")
    def apply_environment_policy(self) -> "Settings":
        if "debug" not in self.model_fields_set:
            self.debug = self.environment == Environment.DEVELOPMENT
        if "log_level" not in self.model_fields_set:
            self.log_level = "DEBUG" if self.environment == Environment.DEVELOPMENT else "INFO"
        if self.environment == Environment.TEST:
            self.debug = False
        if self.environment == Environment.PRODUCTION:
            self._validate_production_safety()
        return self

    def _validate_production_safety(self) -> None:
        unsafe_settings: list[str] = []
        if self.debug:
            unsafe_settings.append("APP_DEBUG must be false")
        if self.postgres_password.get_secret_value() == "commerce":
            unsafe_settings.append("POSTGRES_PASSWORD must not use the default value")
        if self.postgres_host in {"localhost", "127.0.0.1"}:
            unsafe_settings.append("POSTGRES_HOST must not point to localhost")
        if "localhost" in self.elasticsearch_url or "127.0.0.1" in self.elasticsearch_url:
            unsafe_settings.append("ELASTICSEARCH_URL must not point to localhost")
        if "localhost" in self.redis_url or "127.0.0.1" in self.redis_url:
            unsafe_settings.append("REDIS_URL must not point to localhost")
        if (
            "localhost" in self.kafka_bootstrap_servers
            or "127.0.0.1" in self.kafka_bootstrap_servers
        ):
            unsafe_settings.append("KAFKA_BOOTSTRAP_SERVERS must not point to localhost")

        if unsafe_settings:
            details = "; ".join(unsafe_settings)
            raise ValueError(f"Unsafe production configuration: {details}")

    @property
    def docs_enabled(self) -> bool:
        return self.environment != Environment.PRODUCTION

    @property
    def log_format(self) -> Literal["json", "console"]:
        if self.configured_log_format is not None:
            return self.configured_log_format
        return "console" if self.environment == Environment.DEVELOPMENT else "json"

    @property
    def is_test(self) -> bool:
        return self.environment == Environment.TEST

    @property
    def kafka_servers(self) -> list[str]:
        return [
            server.strip() for server in self.kafka_bootstrap_servers.split(",") if server.strip()
        ]


def load_settings(environment: Environment | str | None = None) -> Settings:
    selected_environment = (
        Environment(_normalize_environment(environment))
        if environment is not None
        else EnvironmentSelector().environment
    )
    environment_file = PROJECT_ROOT / f".env.{selected_environment.value}"
    return Settings(
        _env_file=(BASE_ENV_FILE, environment_file),
        environment=selected_environment,
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()

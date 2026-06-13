from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="commerce-search", validation_alias="APP_NAME")
    environment: Literal["local", "test", "staging", "production"] = Field(
        default="local", validation_alias="APP_ENV"
    )
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    log_level: str = Field(default="INFO", validation_alias="APP_LOG_LEVEL")
    api_prefix: str = Field(default="/api/v1", validation_alias="APP_API_PREFIX")

    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="commerce_search", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="commerce", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="commerce", validation_alias="POSTGRES_PASSWORD")

    elasticsearch_url: str = Field(
        default="http://localhost:9200", validation_alias="ELASTICSEARCH_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", validation_alias="KAFKA_BOOTSTRAP_SERVERS"
    )

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

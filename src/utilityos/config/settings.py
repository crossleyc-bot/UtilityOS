"""Environment-based configuration for UtilityOS."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """PostgreSQL database connection settings."""

    model_config = SettingsConfigDict(env_prefix="UTILITYOS_DB_")

    host: str = "localhost"
    port: int = 5432
    name: str = "utilityos"
    user: str = "utilityos"
    password: str = ""
    schema_bronze: str = "bronze"
    schema_silver: str = "silver"
    schema_gold: str = "gold"
    schema_meta: str = "meta"

    @property
    def url(self) -> str:
        """Build the SQLAlchemy connection URL."""
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class PipelineSettings(BaseSettings):
    """Pipeline execution settings."""

    model_config = SettingsConfigDict(env_prefix="UTILITYOS_PIPELINE_")

    batch_size: int = 10000
    max_retries: int = 3
    data_directory: str = "/data"


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="UTILITYOS_LOG_")

    level: str = "INFO"
    json_output: bool = False


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(env_prefix="UTILITYOS_")

    environment: str = "development"
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings()

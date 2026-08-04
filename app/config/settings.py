"""
Centralized application configuration using Pydantic Settings.

All values are loaded from environment variables (or a local .env file
during development). Nothing here is ever hardcoded — this is critical
because the app is deployed on a PaaS (Render, Koyeb, etc.) where PORT and
other values are
injected at runtime.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TelegramSettings(BaseSettings):
    """Telegram Bot API + Webhook related settings."""

    model_config = SettingsConfigDict(
        env_prefix="TELEGRAM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr = Field(..., description="Telegram Bot API token from @BotFather")
    storage_channel_id: int = Field(
        ..., description="Channel ID where source videos are stored (bot must be admin)"
    )

    # Webhook
    webhook_base_url: str = Field(
        ..., description="Public base URL of the deployed service, e.g. https://app.onrender.com"
    )
    webhook_path: str = Field(default="/webhook/telegram")
    webhook_secret_token: SecretStr = Field(
        ..., description="Secret token Telegram sends in X-Telegram-Bot-Api-Secret-Token header"
    )

    # Mini App (optional — only needed if the Telegram Mini App frontend
    # is deployed). Leave unset to disable the "Mở Mini App" button.
    miniapp_url: str | None = Field(
        default=None,
        description="Public URL of the deployed Mini App frontend, e.g. https://user.github.io/repo/",
    )

    @property
    def webhook_url(self) -> str:
        return f"{self.webhook_base_url.rstrip('/')}{self.webhook_path}"

    @field_validator("storage_channel_id")
    @classmethod
    def validate_channel_id(cls, v: int) -> int:
        # Telegram channel IDs are negative and typically start with -100
        if v >= 0:
            raise ValueError("storage_channel_id must be a negative Telegram channel id")
        return v


class DatabaseSettings(BaseSettings):
    """Supabase PostgreSQL connection settings (asyncpg driver)."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: SecretStr = Field(
        ...,
        description=(
            "Full async SQLAlchemy DSN, e.g. " "postgresql+asyncpg://user:pass@host:5432/postgres"
        ),
    )
    pool_size: int = Field(default=5, ge=1, le=50)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=1)
    echo: bool = Field(default=False)


class RedisSettings(BaseSettings):
    """Redis connection settings (optional — can be disabled)."""

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(default=False)
    url: str = Field(default="redis://localhost:6379/0")


class AppSettings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Field(default=Environment.LOCAL)
    debug: bool = Field(default=False)
    port: int = Field(default=8000, description="Injected by the hosting platform via PORT env var")
    log_level: str = Field(default="INFO")
    log_dir: str = Field(default="logs")

    # Admin — raw comma-separated string from env (e.g. "111,222,333"),
    # exposed as a parsed list via the `admin_ids` property below.
    # Kept as `str` at the field level because pydantic-settings attempts
    # JSON-decoding for complex-typed env vars before validators run,
    # which breaks plain comma-separated input.
    admin_ids_raw: str = Field(default="", alias="ADMIN_IDS")

    # Security
    rate_limit_per_minute: int = Field(default=20, ge=1)

    @property
    def admin_ids(self) -> list[int]:
        if not self.admin_ids_raw.strip():
            return []
        return [int(x.strip()) for x in self.admin_ids_raw.split(",") if x.strip()]

    telegram: TelegramSettings = Field(default_factory=TelegramSettings)  # type: ignore[arg-type]
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)  # type: ignore[arg-type]
    redis: RedisSettings = Field(default_factory=RedisSettings)


@lru_cache
def get_settings() -> AppSettings:
    """Cached settings accessor — safe to call repeatedly across the app."""
    return AppSettings()

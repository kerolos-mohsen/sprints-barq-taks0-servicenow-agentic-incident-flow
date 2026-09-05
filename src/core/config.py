"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and parse .env file.
Crashes on startup if any required variable is missing (fail-fast).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration for the incident agent service."""

    # Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ServiceNow PDI
    SERVICENOW_INSTANCE_URL: str
    SERVICENOW_USERNAME: str
    SERVICENOW_PASSWORD: str

    # Webhook security
    WEBHOOK_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton.

    Raises ValidationError on first call if any required env var is missing.
    """
    return Settings()

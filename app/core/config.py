"""Central application configuration using pydantic-settings.

Loads and validates all environment variables at startup.
A missing or invalid variable raises an error immediately (fail-fast).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings sourced from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Database ---
    DATABASE_URL: str

    # --- JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "https://127.0.0.1:5173",
    ]
    CORS_ORIGIN_REGEX: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    # --- Webhooks ---
    # Must be set in production to authenticate gateway callbacks.
    WEBHOOK_SECRET: str | None = None

    # --- Environment ---
    ENVIRONMENT: str = "development"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Reject weak secret keys that could allow JWT forgery.

        Args:
            v: The raw SECRET_KEY value from the environment.

        Returns:
            The validated key string.

        Raises:
            ValueError: If the key is shorter than 32 characters.
        """
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate a strong one with: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v

    @property
    def is_production(self) -> bool:
        """Return True when running in the production environment."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()


settings: Settings = get_settings()

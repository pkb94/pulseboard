"""
CORE — app/core/config.py
──────────────────────────
LESSON: Pydantic Settings reads config from environment variables
and .env files automatically. Fail-fast at startup if required vars
are missing — never silently use wrong config in production.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Security
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # App
    app_name: str = "PulseBoard API"
    version: str = "1.0.0"
    debug: bool = False

    # Simulator
    simulator_interval_seconds: float = 1.0
    heartbeat_interval_seconds: float = 30.0


settings = Settings()

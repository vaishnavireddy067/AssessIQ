"""
Application configuration via pydantic-settings.
All values sourced from environment variables / .env file.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "assessiq-super-secret-development-key-32-chars-min"
    APP_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).resolve().parent / 'assessiq.db'}"
    DATABASE_URL_SYNC: str = f"sqlite:///{Path(__file__).resolve().parent / 'assessiq.db'}"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # ── Storage ────────────────────────────────────────────────────────────────
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_PATH: str = "/app/uploads"

    # ── Email ──────────────────────────────────────────────────────────────────
    EMAIL_PROVIDER: str = "console"
    EMAIL_FROM: str = "noreply@assessiq.io"

    # ── Super Admin seed ───────────────────────────────────────────────────────
    SUPER_ADMIN_EMAIL: str = "admin@assessiq.io"
    SUPER_ADMIN_PASSWORD: str = "CHANGE_ME"

    # ── Feature flags ──────────────────────────────────────────────────────────
    FEATURE_AI_COPILOT: bool = False
    FEATURE_PROCTORING: bool = False
    FEATURE_CODING_RUNNER: bool = False


settings = Settings()

"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and type-check all configuration values.
Access the singleton settings instance via `get_settings()`.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All values have sensible defaults for local development.
    In production, override via environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/asset_management"

    # Redis (used by Celery broker and result backend)
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # File upload limits
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB in bytes

    # Batch processing
    BATCH_SIZE: int = 100

    # Pagination
    PAGE_SIZE_DEFAULT: int = 25
    PAGE_SIZE_MAX: int = 500


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance.

    Uses lru_cache so the settings are loaded once and reused
    across the application lifetime.
    """
    return Settings()

"""Tests for app.core.config module."""

import os
from unittest.mock import patch

from app.core.config import Settings, get_settings


class TestSettings:
    """Test the Settings class and defaults."""

    def test_default_database_url(self):
        s = Settings()
        assert s.DATABASE_URL == "postgresql+asyncpg://postgres:postgres@localhost:5432/asset_management"

    def test_default_redis_url(self):
        s = Settings()
        assert s.REDIS_URL == "redis://localhost:6379/0"

    def test_default_cors_origins(self):
        s = Settings()
        assert "http://localhost:5173" in s.CORS_ORIGINS
        assert "http://localhost:3000" in s.CORS_ORIGINS

    def test_default_max_upload_size(self):
        s = Settings()
        assert s.MAX_UPLOAD_SIZE == 50 * 1024 * 1024  # 50 MB

    def test_default_batch_size(self):
        s = Settings()
        assert s.BATCH_SIZE == 100

    def test_default_page_size(self):
        s = Settings()
        assert s.PAGE_SIZE_DEFAULT == 25

    def test_default_page_size_max(self):
        s = Settings()
        assert s.PAGE_SIZE_MAX == 500

    def test_env_override(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://u:p@host/db"}):
            s = Settings()
            assert s.DATABASE_URL == "postgresql+asyncpg://u:p@host/db"

    def test_batch_size_override(self):
        with patch.dict(os.environ, {"BATCH_SIZE": "200"}):
            s = Settings()
            assert s.BATCH_SIZE == 200

    def test_cors_origins_from_env_json(self):
        with patch.dict(os.environ, {"CORS_ORIGINS": '["https://example.com"]'}):
            s = Settings()
            assert s.CORS_ORIGINS == ["https://example.com"]


class TestGetSettings:
    """Test the singleton accessor."""

    def test_returns_settings_instance(self):
        s = get_settings()
        assert isinstance(s, Settings)

    def test_singleton_returns_same_instance(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

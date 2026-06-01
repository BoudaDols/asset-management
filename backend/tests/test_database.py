"""Tests for app.core.database module.

Tests verify module structure, configuration, and behavior without
requiring a live database connection.
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import (
    Base,
    async_session_factory,
    check_db_health,
    engine,
    get_db,
)


class TestEngineConfiguration:
    """Tests for the async SQLAlchemy engine setup."""

    def test_engine_is_async(self):
        """Engine should be an async engine instance."""
        # create_async_engine returns an AsyncEngine
        assert engine is not None
        assert "asyncpg" in str(engine.url) or "postgresql" in str(engine.url)

    def test_engine_pool_size(self):
        """Engine should be configured with pool_size=5."""
        assert engine.pool.size() == 5

    def test_engine_max_overflow(self):
        """Engine should be configured with max_overflow=10."""
        assert engine.pool._max_overflow == 10


class TestSessionFactory:
    """Tests for the async session factory."""

    def test_session_factory_exists(self):
        """Session factory should be an async_sessionmaker instance."""
        assert async_session_factory is not None
        assert isinstance(async_session_factory, async_sessionmaker)

    def test_session_factory_produces_async_session(self):
        """Session factory should produce AsyncSession instances."""
        session = async_session_factory()
        assert isinstance(session, AsyncSession)
        # Clean up
        import asyncio

        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(session.close())


class TestBase:
    """Tests for the declarative Base class."""

    def test_base_is_declarative_base(self):
        """Base should be a DeclarativeBase subclass."""
        from sqlalchemy.orm import DeclarativeBase

        assert issubclass(Base, DeclarativeBase)

    def test_base_has_metadata(self):
        """Base should have a metadata attribute for table definitions."""
        assert Base.metadata is not None


class TestGetDb:
    """Tests for the get_db FastAPI dependency."""

    @pytest.mark.asyncio
    async def test_get_db_yields_session(self):
        """get_db should yield an AsyncSession instance."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch(
            "app.core.database.async_session_factory",
            return_value=mock_session,
        ):
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            gen = get_db()
            session = await gen.__anext__()
            assert session is mock_session

    @pytest.mark.asyncio
    async def test_get_db_commits_on_success(self):
        """get_db should commit the session when no exception occurs."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        with patch(
            "app.core.database.async_session_factory",
        ) as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            gen = get_db()
            session = await gen.__anext__()
            # Simulate successful completion
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_session.commit.assert_called_once()
            mock_session.rollback.assert_not_called()


class TestCheckDbHealth:
    """Tests for the database health check function."""

    @pytest.mark.asyncio
    async def test_health_check_returns_true_on_success(self):
        """check_db_health should return True when DB is reachable."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_conn
        mock_cm.__aexit__.return_value = None

        with patch("app.core.database.engine") as mock_engine:
            mock_engine.connect.return_value = mock_cm

            result = await check_db_health()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_returns_false_on_failure(self):
        """check_db_health should return False when DB is unreachable."""
        with patch("app.core.database.engine") as mock_engine:
            mock_engine.connect = AsyncMock(side_effect=Exception("Connection refused"))

            result = await check_db_health()
            assert result is False

"""Async database engine, session factory, and utilities.

Provides:
- Async SQLAlchemy engine configured with asyncpg and connection pooling
- AsyncSession factory for dependency injection
- `get_db` FastAPI dependency yielding an AsyncSession
- `check_db_health` function for the /api/v1/health endpoint
- `Base` declarative base class for all SQLAlchemy models
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models."""

    pass


settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage in route handlers:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically closed after the request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Test database connectivity by executing a simple query.

    Returns True if the database is reachable, False otherwise.
    Used by the /api/v1/health endpoint to determine service availability.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

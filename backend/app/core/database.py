"""Database-per-tenant architecture with a central shared database.

Architecture:
- Central DB: holds catalog hierarchy, tenant registry, users
- Tenant DBs: one Aurora PostgreSQL instance per tenant for asset data

Provides:
- Central async engine/session for shared data (catalog, tenants, auth)
- TenantDBManager: maintains a dict of engines keyed by tenant_code
- `get_central_db()` FastAPI dependency for catalog/auth routes
- `get_tenant_db(tenant_code)` dependency for tenant-scoped routes
- `check_db_health()` for the /api/v1/health endpoint
- `Base` declarative base class for all SQLAlchemy models
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
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

# --- Central Database Engine (catalog, tenants, users) ---

central_engine = create_async_engine(
    settings.CENTRAL_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)

central_session_factory = async_sessionmaker(
    bind=central_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_central_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session to the central database.

    Use for catalog, tenant registry, and auth routes.

    Usage:
        @router.get("/catalog/services")
        async def list_services(db: AsyncSession = Depends(get_central_db)):
            ...
    """
    async with central_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Backward-compatible alias — existing routes using `get_db` continue to work
# against the central database until migrated to tenant-scoped sessions.
get_db = get_central_db


# --- Tenant Database Manager ---


class TenantDBManager:
    """Manages per-tenant database connections.

    Maintains a dictionary of async engines keyed by tenant_code.
    Each tenant's database_url is stored in the central DB's tenant_ville table.
    """

    def __init__(self) -> None:
        self._engines: dict[str, AsyncEngine] = {}
        self._session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}

    def _create_engine(self, database_url: str) -> AsyncEngine:
        """Create an async engine with a small connection pool for a single tenant."""
        return create_async_engine(
            database_url,
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            echo=False,
        )

    async def get_engine(self, tenant_code: str) -> AsyncEngine:
        """Get or create an engine for the given tenant.

        On first call for a tenant, looks up the database_url from the central DB
        and caches the engine for subsequent requests.
        """
        if tenant_code in self._engines:
            return self._engines[tenant_code]

        # Look up tenant's database_url from central DB
        async with central_session_factory() as session:
            result = await session.execute(
                text(
                    "SELECT database_url FROM tenant_ville "
                    "WHERE tenant_code = :code AND is_active = true"
                ),
                {"code": tenant_code},
            )
            row = result.fetchone()

        if row is None or row[0] is None:
            raise ValueError(
                f"Tenant '{tenant_code}' not found or database not yet provisioned"
            )

        database_url: str = row[0]
        engine = self._create_engine(database_url)
        self._engines[tenant_code] = engine
        self._session_factories[tenant_code] = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        return engine

    async def get_session(self, tenant_code: str) -> AsyncSession:
        """Get a new session for the given tenant's database."""
        if tenant_code not in self._session_factories:
            await self.get_engine(tenant_code)
        return self._session_factories[tenant_code]()

    async def dispose_all(self) -> None:
        """Dispose all tenant engines (call on shutdown)."""
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._session_factories.clear()

    async def dispose_tenant(self, tenant_code: str) -> None:
        """Dispose a specific tenant's engine (e.g., after deprovisioning)."""
        if tenant_code in self._engines:
            await self._engines[tenant_code].dispose()
            del self._engines[tenant_code]
            del self._session_factories[tenant_code]


# Singleton instance
tenant_db_manager = TenantDBManager()


async def get_tenant_db(tenant_code: str) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async session to a tenant's database.

    Usage:
        @router.get("/tenants/{tenant_code}/assets")
        async def list_assets(
            tenant_code: str,
            db: AsyncSession = Depends(lambda tc=tenant_code: get_tenant_db(tc)),
        ):
            ...
    """
    session = await tenant_db_manager.get_session(tenant_code)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# --- Health Check ---


async def check_db_health() -> bool:
    """Test central database connectivity by executing a simple query.

    Returns True if the central database is reachable, False otherwise.
    Used by the /api/v1/health endpoint to determine service availability.
    """
    try:
        async with central_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

"""Municipal Asset Management System - FastAPI Application Entry Point."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers

settings = get_settings()

app = FastAPI(
    title="Municipal Asset Management System",
    description=(
        "REST API for managing municipal infrastructure assets organized "
        "in a strict 8-level hierarchy. Supports asset catalog management, "
        "manual data entry, Excel bulk import, and report generation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register custom exception handlers
register_exception_handlers(app)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Versioned API Router ---

api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get(
    "/health",
    summary="Health Check",
    description=(
        "Returns service health status. Returns 200 when the database "
        "connection is available and 503 when it is not."
    ),
    response_model=dict,
)
async def health_check() -> JSONResponse:
    """Health check endpoint.

    Returns 200 when the database is reachable.
    Returns 503 with error_code SERVICE_UNAVAILABLE when the database is down.
    """
    from app.core.database import check_db_health

    db_healthy = await check_db_health()

    if db_healthy:
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "municipal-asset-management",
                "version": "1.0.0",
                "database": "connected",
            },
        )

    return JSONResponse(
        status_code=503,
        content={
            "status": "unhealthy",
            "error_code": "SERVICE_UNAVAILABLE",
            "message": "Database connection failed",
            "service": "municipal-asset-management",
            "version": "1.0.0",
            "database": "disconnected",
        },
    )


# Include the versioned router in the app
app.include_router(api_v1_router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint redirecting to API documentation."""
    return {
        "message": "Municipal Asset Management System API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health",
    }

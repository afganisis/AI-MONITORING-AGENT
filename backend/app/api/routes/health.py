"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from loguru import logger

from app.database.session import get_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.

    Returns:
        Status of API and database connectivity
    """
    status = {
        "api": "healthy",
        "database": "unknown",
        "zeroeld_api": settings.zeroeld_api_url,
    }

    # Check database connectivity
    try:
        result = await db.execute(text("SELECT 1"))
        if result:
            status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status["database"] = "unhealthy"
        status["api"] = "degraded"

    return status


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}

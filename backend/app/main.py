"""FastAPI main application."""

import sys
import asyncio
import platform

# CRITICAL: Fix Playwright subprocess on Windows
# Must be set before FastAPI and other imports
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import get_settings
from app.database.session import engine, Base

# Import models to register them with Base
from app.database import models  # noqa: F401

# Import routers
from app.api.routes import health, agent, errors, fixes, websocket as ws_route, companies, auth

# Import agent service
from app.agent.background_service import agent_service

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="ZeroELD AI Agent API",
    description="AI Agent for automatically fixing ELD compliance errors",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
allowed_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    logger.info("Starting ZeroELD AI Agent API...")
    logger.info(f"Environment: {'DEBUG' if settings.debug else 'PRODUCTION'}")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    logger.info(f"Fortex API: {settings.fortex_api_url}")
    logger.info(f"Fortex UI: {settings.fortex_ui_url}")
    logger.info(f"CORS Origins: {allowed_origins}")

    # Create database tables
    async with engine.begin() as conn:
        # Don't drop tables in production
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables initialized")

    # Note: Agent service is NOT auto-started
    # It must be started manually via /api/agent/start endpoint
    logger.info("Agent service initialized (not started)")

    # Start Telegram bot
    try:
        from app.telegram.bot_service import telegram_bot
        await telegram_bot.start()
    except Exception as e:
        logger.warning(f"Telegram bot failed to start: {e}")

    logger.info("API is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down ZeroELD AI Agent API...")

    # Stop Telegram bot
    try:
        from app.telegram.bot_service import telegram_bot
        await telegram_bot.stop()
    except Exception as e:
        logger.warning(f"Telegram bot shutdown error: {e}")

    # Stop agent service if running
    if agent_service.is_running:
        logger.info("Stopping agent service...")
        await agent_service.stop()
        await agent_service.cleanup()

    await engine.dispose()
    logger.info("Shutdown complete")


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(errors.router, prefix="/api/errors", tags=["Errors"])
app.include_router(fixes.router, prefix="/api/fixes", tags=["Fixes"])
app.include_router(companies.router, prefix="/api", tags=["Companies"])
app.include_router(ws_route.router, tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "ZeroELD AI Agent API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    # NOTE: For Playwright to work on Windows, use run_server.py instead
    # This block is for development only
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )

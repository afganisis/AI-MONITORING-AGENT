"""Initialize database - create all tables."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.session import init_db
from loguru import logger


async def main():
    """Create all database tables."""
    logger.info("Initializing database...")

    try:
        await init_db()
        logger.success("✓ Database initialized successfully!")
        logger.info("All tables created.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

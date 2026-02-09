"""Script to create the initial admin user."""

import asyncio
import sys
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("\\", 2)[0])

from app.database.session import get_db_session, init_db
from app.services.auth_service import create_user, get_user_by_username


async def create_initial_user():
    """Create the initial admin user."""
    # First, ensure database tables are created
    logger.info("Initializing database tables...")
    await init_db()
    logger.success("✓ Database tables ready")

    username = "admin"
    email = "admin@zeroeld.com"
    password = "admin123"
    full_name = "Administrator"

    async with get_db_session() as db:
        # Check if admin user already exists
        existing_user = await get_user_by_username(db, username)
        if existing_user:
            logger.info(f"Admin user '{username}' already exists")
            return existing_user

        # Create admin user
        user = await create_user(
            db,
            username=username,
            email=email,
            password=password,
            full_name=full_name,
            is_superuser=True,
        )

        if user:
            logger.info(f"Admin user created successfully!")
            logger.info(f"  Username: {user.username}")
            logger.info(f"  Email: {user.email}")
            logger.info(f"  Full Name: {user.full_name}")
            logger.info(f"  Is Superuser: {user.is_superuser}")
            return user
        else:
            logger.error("Failed to create admin user")
            return None


if __name__ == "__main__":
    logger.info("Creating initial admin user...")
    user = asyncio.run(create_initial_user())
    if user:
        logger.success("Initial user creation completed!")
        sys.exit(0)
    else:
        logger.error("Initial user creation failed!")
        sys.exit(1)

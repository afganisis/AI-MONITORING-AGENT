"""Authentication service for user management and JWT token handling."""

from datetime import datetime, timedelta
from typing import Optional
import uuid

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.config import get_settings
from app.database.models import User

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # Convert password to bytes and hash it
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of claims if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except JWTError as e:
        logger.debug(f"Invalid token: {e}")
        return None


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        User object if authentication successful, None otherwise
    """
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: UUID of user to fetch

    Returns:
        User object or None
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return None

    result = await db.execute(select(User).where(User.id == user_uuid))
    return result.scalars().first()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get a user by username.

    Args:
        db: Database session
        username: Username to fetch

    Returns:
        User object or None
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email.

    Args:
        db: Database session
        email: Email to fetch

    Returns:
        User object or None
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_superuser: bool = False,
) -> Optional[User]:
    """
    Create a new user.

    Args:
        db: Database session
        username: Unique username
        email: Unique email address
        password: Plain text password (will be hashed)
        full_name: Optional full name
        is_superuser: Whether user is a superuser

    Returns:
        Created User object or None if creation failed
    """
    # Check if user already exists
    existing_user = await get_user_by_username(db, username)
    if existing_user:
        logger.warning(f"Username '{username}' already exists")
        return None

    existing_email = await get_user_by_email(db, email)
    if existing_email:
        logger.warning(f"Email '{email}' already exists")
        return None

    # Create new user
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        is_superuser=is_superuser,
        is_active=True,
    )

    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        logger.info(f"User created: {username} ({email})")
        return user
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create user {username}: {e}")
        return None


async def update_user_last_login(db: AsyncSession, user: User) -> None:
    """
    Update the last_login_at timestamp for a user.

    Args:
        db: Database session
        user: User object to update
    """
    user.last_login_at = datetime.utcnow()
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update last login for {user.username}: {e}")


async def deactivate_user(db: AsyncSession, user: User) -> bool:
    """
    Deactivate a user account.

    Args:
        db: Database session
        user: User object to deactivate

    Returns:
        True if successful, False otherwise
    """
    user.is_active = False
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        logger.info(f"User deactivated: {user.username}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to deactivate user {user.username}: {e}")
        return False


async def change_password(db: AsyncSession, user: User, new_password: str) -> bool:
    """
    Change a user's password.

    Args:
        db: Database session
        user: User object
        new_password: New plain text password

    Returns:
        True if successful, False otherwise
    """
    user.password_hash = hash_password(new_password)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        logger.info(f"Password changed for user: {user.username}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to change password for {user.username}: {e}")
        return False

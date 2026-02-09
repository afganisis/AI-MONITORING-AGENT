"""Authentication endpoints."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.session import get_db
from app.database.models import User
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token,
    update_user_last_login,
)
from app.api.dependencies import get_current_user
from app.config import get_settings

router = APIRouter()
settings = get_settings()


# Pydantic models
class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, max_length=255)


class UserUpdate(BaseModel):
    """User update schema."""

    full_name: str | None = None
    email: EmailStr | None = None


class UserResponse(UserBase):
    """User response schema."""

    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Token response with access token and user info

    Raises:
        HTTPException: If username or email already exists
    """
    # Create the new user
    new_user = await create_user(
        db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        is_superuser=False,
    )

    if not new_user:
        logger.warning(f"Registration failed for {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    # Update last login
    await update_user_last_login(db, new_user)

    # Create token
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    logger.info(f"New user registered: {new_user.username}")

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    Args:
        credentials: Login credentials (username and password)
        db: Database session

    Returns:
        Token response with access token and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    # Authenticate user
    user = await authenticate_user(db, credentials.username, credentials.password)

    if not user:
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login timestamp
    await update_user_last_login(db, user)

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at.isoformat(),
        updated_at=current_user.updated_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Logout endpoint (for client-side tracking).

    This endpoint is primarily for frontend to know logout was successful.
    Token invalidation is handled by not storing tokens on the server.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Logout successful"}

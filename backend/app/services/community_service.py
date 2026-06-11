"""Service for community user operations"""
import secrets
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User, UserRole, UserType
from app.core.security import hash_password, verify_password
from app.core.config import settings
from jose import JWTError, jwt


def generate_referral_code() -> str:
    """
    Generate a unique 8-character alphanumeric referral code.
    
    Returns:
        str: 8-character alphanumeric code (uppercase)
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(8))


async def check_referral_code_unique(db: AsyncSession, code: str) -> bool:
    """
    Check if a referral code is unique in the database.
    
    Args:
        db: Database session
        code: Referral code to check
        
    Returns:
        bool: True if code is unique, False otherwise
    """
    result = await db.execute(
        select(User).where(User.referral_code == code)
    )
    existing_user = result.scalar_one_or_none()
    return existing_user is None


async def generate_unique_referral_code(db: AsyncSession, max_retries: int = 5) -> str:
    """
    Generate a unique referral code with collision checking.
    
    Args:
        db: Database session
        max_retries: Maximum number of retry attempts
        
    Returns:
        str: Unique 8-character referral code
        
    Raises:
        HTTPException: If unable to generate unique code after max_retries
    """
    for _ in range(max_retries):
        code = generate_referral_code()
        if await check_referral_code_unique(db, code):
            return code
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to generate unique referral code. Please try again."
    )


def generate_verification_token(user_id: UUID) -> str:
    """
    Generate JWT token for email verification.
    
    Args:
        user_id: User's UUID
        
    Returns:
        str: JWT token with 24-hour expiration
    """
    expiration = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "user_id": str(user_id),
        "type": "email_verification",
        "exp": expiration
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def verify_verification_token(token: str) -> Optional[UUID]:
    """
    Verify and decode email verification token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        UUID: User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "email_verification":
            return None
        user_id = UUID(payload.get("user_id"))
        return user_id
    except (JWTError, ValueError):
        return None


def generate_password_reset_token(user_id: UUID) -> str:
    """
    Generate JWT token for password reset.
    
    Args:
        user_id: User's UUID
        
    Returns:
        str: JWT token with 1-hour expiration
    """
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "user_id": str(user_id),
        "type": "password_reset",
        "exp": expiration
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def verify_password_reset_token(token: str) -> Optional[UUID]:
    """
    Verify and decode password reset token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        UUID: User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            return None
        user_id = UUID(payload.get("user_id"))
        return user_id
    except (JWTError, ValueError):
        return None


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email address.
    
    Args:
        db: Database session
        email: User's email
        
    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get user by username.
    
    Args:
        db: Database session
        username: User's username
        
    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_referral_code(db: AsyncSession, referral_code: str) -> Optional[User]:
    """
    Get user by referral code.
    
    Args:
        db: Database session
        referral_code: Referral code
        
    Returns:
        User: User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.referral_code == referral_code)
    )
    return result.scalar_one_or_none()


async def create_community_user(
    db: AsyncSession,
    email: str,
    password: str,
    username: str,
    registration_ip: str,
    referral_code: Optional[str] = None
) -> User:
    """
    Create a new community user account.
    
    Args:
        db: Database session
        email: User's email
        password: User's password (will be hashed)
        username: User's public username
        registration_ip: IP address of registration
        referral_code: Optional referral code from another user
        
    Returns:
        User: Created user object
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="EMAIL_ALREADY_EXISTS"
        )
    
    # Check if username already exists
    existing_username = await get_user_by_username(db, username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="USERNAME_ALREADY_EXISTS"
        )
    
    # Validate and get referrer if referral code provided
    referred_by_id = None
    if referral_code:
        referrer = await get_user_by_referral_code(db, referral_code)
        if not referrer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="INVALID_REFERRAL_CODE"
            )
        referred_by_id = referrer.id
    
    # Generate unique referral code for new user
    user_referral_code = await generate_unique_referral_code(db)
    
    # Hash password
    password_hash = hash_password(password)
    
    # Generate ID for verification token
    user_id = uuid.uuid4()
    
    # Create user
    new_user = User(
        id=user_id,
        name=username,  # Use username as name for community users
        email=email,
        password_hash=password_hash,
        username=username,
        role=UserRole.COMMUNITY_USER,
        user_type=UserType.COMMUNITY_USER,
        email_verified=False,
        referral_code=user_referral_code,
        referred_by_id=referred_by_id,
        registration_ip=registration_ip,
        is_active=True,
        points=0.0,
        xp=0.0,
        level=1,
        current_streak=0
    )
    # Generate and persist email verification token and timestamp
    try:
        new_user.email_verification_token = generate_verification_token(user_id)
        new_user.email_verification_sent_at = datetime.utcnow()
    except Exception:
        # If token generation fails for any reason, proceed without blocking user creation
        new_user.email_verification_token = None
        new_user.email_verification_sent_at = None

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

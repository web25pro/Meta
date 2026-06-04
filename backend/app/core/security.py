"""Security utilities for authentication and authorization"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: str
    role: str
    user_type: str
    iat: datetime
    exp: datetime


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, role: str, user_type: str) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User ID
        role: User role
        user_type: User type
        
    Returns:
        str: JWT token
    """
    now = datetime.utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "user_id": user_id,
        "role": role,
        "user_type": user_type,
        "iat": now,
        "exp": expire,
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        user_id: User ID
        
    Returns:
        str: JWT refresh token
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT access token.
    
    Args:
        token: JWT token
        
    Returns:
        TokenData: Decoded token data, or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id = payload.get("user_id")
        role = payload.get("role")
        user_type = payload.get("user_type")
        
        if user_id is None or role is None or user_type is None:
            return None
        
        return TokenData(
            user_id=user_id,
            role=role,
            user_type=user_type,
            iat=datetime.fromtimestamp(payload.get("iat")),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify and decode a JWT refresh token.
    
    Args:
        token: JWT refresh token
        
    Returns:
        str: User ID, or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            return None
        
        return payload.get("user_id")
    except JWTError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        return None

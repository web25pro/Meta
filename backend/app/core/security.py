"""Security utilities for authentication and authorization"""
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Workaround for passlib/bcrypt compatibility issue with bcrypt >= 4.0.0
# bcrypt 4.0.0 removed __about__ which passlib 1.7.4 expects
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('About', (object,), {'__version__': bcrypt.__version__})

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: str
    role: str
    user_type: str
    iat: datetime
    exp: datetime


def hash_password(password: Union[str, bytes]) -> str:
    """
    Hash a password using bcrypt.
    
    Bcrypt has a 72-byte limit for passwords. If exceeded, passlib raises a ValueError.
    We truncate the password to 72 bytes to avoid this and maintain compatibility.
    
    Args:
        password: Plain text password (str or bytes)
        
    Returns:
        str: Hashed password
    """
    if isinstance(password, str):
        pw_bytes = password.encode("utf-8")
    else:
        pw_bytes = password
        
    # Truncate to 72 bytes for bcrypt compatibility
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
        
    return pwd_context.hash(pw_bytes)


def verify_password(plain_password: Union[str, bytes], hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password (str or bytes)
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    if isinstance(plain_password, str):
        pw_bytes = plain_password.encode("utf-8")
    else:
        pw_bytes = plain_password
        
    # Truncate to 72 bytes for bcrypt compatibility
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
        
    return pwd_context.verify(pw_bytes, hashed_password)


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

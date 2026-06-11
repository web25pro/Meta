"""Pydantic schemas for community user operations"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class CommunityUserRegisterRequest(BaseModel):
    """Schema for community user registration request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=72, description="User's password (min 8 characters, max 72 for bcrypt)")
    username: str = Field(..., min_length=3, max_length=20, description="Public display name")
    referral_code: Optional[str] = Field(None, min_length=8, max_length=8, description="Optional referral code")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters and underscores"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class CommunityUserResponse(BaseModel):
    """Schema for community user response (public fields only)"""
    id: UUID
    email: str
    username: str
    email_verified: bool
    referral_code: str
    points: float
    xp: float
    level: int
    current_streak: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    token: str = Field(..., description="Email verification JWT token")


class EmailVerificationResponse(BaseModel):
    """Schema for email verification response"""
    message: str
    email_verified: bool


class ReferralCodeResponse(BaseModel):
    """Schema for referral code response"""
    referral_code: str
    referral_link: str


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: CommunityUserResponse


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Schema for password reset response"""
    message: str


class PasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., description="Password reset JWT token")
    new_password: str = Field(..., min_length=8, max_length=72, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordResetConfirmResponse(BaseModel):
    """Schema for password reset confirmation response"""
    message: str

"""Authentication schemas"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


class LoginRequest(BaseModel):
    """
    Login request schema for user authentication.
    
    Requires valid email and password credentials.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePassword123!"
                }
            ]
        }
    )
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User's password",
        examples=["SecurePassword123!"]
    )


class TokenResponse(BaseModel):
    """
    JWT token response after successful authentication.
    
    Contains access token (15-minute expiration) and refresh token (7-day expiration).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 900
                }
            ]
        }
    )
    
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication (15-minute expiration)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens (7-day expiration)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
        examples=["bearer"]
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        examples=[900]
    )


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request for obtaining a new access token.
    
    Use this endpoint when the access token expires.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    )
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token obtained from login",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )


class PasswordResetRequest(BaseModel):
    """
    Password reset request schema.
    
    Initiates password reset flow by sending a reset token to the user's email.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com"
                }
            ]
        }
    )
    
    email: EmailStr = Field(
        ...,
        description="Email address of the account to reset",
        examples=["user@example.com"]
    )


class PasswordResetConfirm(BaseModel):
    """
    Password reset confirmation schema.
    
    Completes password reset using the token sent via email.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "token": "abc123def456",
                    "new_password": "NewSecurePassword123!"
                }
            ]
        }
    )
    
    token: str = Field(
        ...,
        description="Password reset token received via email (1-hour expiration)",
        examples=["abc123def456"]
    )
    new_password: str = Field(
        ...,
        min_length=12,
        description="New password (minimum 12 characters)",
        examples=["NewSecurePassword123!"]
    )


class ChangePasswordRequest(BaseModel):
    """
    Change password request for authenticated users.
    
    Allows users to change their password while logged in.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "current_password": "OldPassword123!",
                    "new_password": "NewSecurePassword123!"
                }
            ]
        }
    )
    
    current_password: str = Field(
        ...,
        description="Current password for verification",
        examples=["OldPassword123!"]
    )
    new_password: str = Field(
        ...,
        min_length=12,
        description="New password (minimum 12 characters)",
        examples=["NewSecurePassword123!"]
    )

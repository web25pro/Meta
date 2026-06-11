"""User schemas"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
import uuid

from app.models import UserRole, UserType


class UserBase(BaseModel):
    """Base user schema with common fields"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full name",
        examples=["John Doe"]
    )
    email: EmailStr = Field(
        ...,
        description="User's email address (must be unique)",
        examples=["john.doe@example.com"]
    )


class UserCreate(UserBase):
    """
    User creation schema for admin operations.
    
    Only accessible by Overall_Admin (all users) or Ambassador_Admin (Ambassadors only).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "password": "SecurePassword123!",
                    "role": "Team_Member",
                    "user_type": "Team_Member"
                }
            ]
        }
    )
    
    password: str = Field(
        ...,
        min_length=12,
        max_length=72,
        description="User's password (min 12, max 72 characters for bcrypt)",
        examples=["SecurePassword123!"]
    )
    role: UserRole = Field(
        ...,
        description="User's role (Overall_Admin, Ambassador_Admin, Team_Member, Ambassador)",
        examples=["Team_Member"]
    )
    user_type: UserType = Field(
        ...,
        description="User's type (Team_Member or Ambassador)",
        examples=["Team_Member"]
    )


class UserUpdate(BaseModel):
    """
    User update schema for modifying user information.
    
    All fields are optional. Only provided fields will be updated.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Jane Doe",
                    "email": "jane.doe@example.com",
                    "role": "Ambassador_Admin",
                    "user_type": "Ambassador"
                }
            ]
        }
    )
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="User's full name",
        examples=["Jane Doe"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="User's email address",
        examples=["jane.doe@example.com"]
    )
    role: Optional[UserRole] = Field(
        None,
        description="User's role",
        examples=["Ambassador_Admin"]
    )
    user_type: Optional[UserType] = Field(
        None,
        description="User's type",
        examples=["Ambassador"]
    )


class UserResponse(UserBase):
    """
    User response schema with full user information.
    
    Includes user ID, role, type, points balance, and timestamps.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "role": "Team_Member",
                    "user_type": "Team_Member",
                    "points": 250.0,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-20T14:45:00Z"
                }
            ]
        }
    )
    
    id: uuid.UUID = Field(
        ...,
        description="Unique user identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    role: UserRole = Field(
        ...,
        description="User's role",
        examples=["Team_Member"]
    )
    user_type: UserType = Field(
        ...,
        description="User's type",
        examples=["Team_Member"]
    )
    points: float = Field(
        ...,
        description="User's current Panda Points (PP) balance",
        examples=[250.0]
    )
    xp: float = Field(
        0.0,
        description="User's current Experience Points (XP)",
        examples=[1200.0]
    )
    level: int = Field(
        1,
        description="User's current level",
        examples=[5]
    )
    current_streak: int = Field(
        0,
        description="User's current daily streak",
        examples=[3]
    )
    last_activity_at: Optional[datetime] = Field(
        None,
        description="Timestamp of user's last activity",
        examples=["2024-01-20T14:45:00Z"]
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        examples=["2024-01-20T14:45:00Z"]
    )


class UserListResponse(BaseModel):
    """
    Paginated user list response.
    
    Contains list of users and pagination metadata.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "users": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "John Doe",
                            "email": "john.doe@example.com",
                            "role": "Team_Member",
                            "user_type": "Team_Member",
                            "points": 250.0,
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-20T14:45:00Z"
                        }
                    ],
                    "total": 50,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    )
    
    users: list[UserResponse] = Field(
        ...,
        description="List of users for current page"
    )
    total: int = Field(
        ...,
        description="Total number of users",
        ge=0,
        examples=[50]
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        ge=1,
        examples=[1]
    )
    page_size: int = Field(
        ...,
        description="Number of users per page",
        ge=1,
        le=100,
        examples=[20]
    )

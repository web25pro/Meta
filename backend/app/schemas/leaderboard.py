"""Leaderboard schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
import uuid


class LeaderboardEntryResponse(BaseModel):
    """Leaderboard entry response schema"""
    user_id: uuid.UUID = Field(..., description="User's unique identifier")
    user_name: str = Field(..., description="User's display name")
    user_type: str = Field(..., description="User type (Team_Member or Ambassador)")
    rank: int = Field(..., description="User's rank in the leaderboard (1 = highest)", ge=1)
    total_pp: float = Field(..., description="User's total Panda Points", ge=0)
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_name": "John Doe",
                "user_type": "Team_Member",
                "rank": 1,
                "total_pp": 1250.5,
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class LeaderboardResponse(BaseModel):
    """Leaderboard response schema"""
    entries: List[LeaderboardEntryResponse] = Field(..., description="List of leaderboard entries")
    total: int = Field(..., description="Total number of users in leaderboard", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Number of entries per page", ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "entries": [
                    {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_name": "John Doe",
                        "user_type": "Team_Member",
                        "rank": 1,
                        "total_pp": 1250.5,
                        "updated_at": "2024-01-15T10:30:00Z"
                    },
                    {
                        "user_id": "223e4567-e89b-12d3-a456-426614174001",
                        "user_name": "Jane Smith",
                        "user_type": "Team_Member",
                        "rank": 2,
                        "total_pp": 980.0,
                        "updated_at": "2024-01-15T10:25:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 20
            }
        }


class UserRankResponse(BaseModel):
    """User rank response schema"""
    user_id: uuid.UUID = Field(..., description="User's unique identifier")
    rank: int = Field(..., description="User's rank in the leaderboard (1 = highest)", ge=1)
    total_pp: float = Field(..., description="User's total Panda Points", ge=0)
    user_type: str = Field(..., description="User type (Team_Member or Ambassador)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "rank": 5,
                "total_pp": 750.0,
                "user_type": "Team_Member"
            }
        }


"""Announcement schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid


class AnnouncementCreateRequest(BaseModel):
    """Announcement creation request schema"""
    title: str = Field(..., min_length=1, max_length=255, description="Announcement title")
    content: str = Field(..., min_length=1, description="Announcement content")
    target_group: str = Field(
        ...,
        description="Target group (Team_Members, Ambassadors, or All)",
        pattern="^(Team_Members|Ambassadors|All)$"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "New Task Deadline Policy",
                "content": "Starting next month, all tasks must be submitted at least 24 hours before the deadline to allow for review time.",
                "target_group": "All"
            }
        }


class AnnouncementUpdateRequest(BaseModel):
    """Announcement update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Announcement title")
    content: Optional[str] = Field(None, min_length=1, description="Announcement content")
    target_group: Optional[str] = Field(
        None,
        description="Target group (Team_Members, Ambassadors, or All)",
        pattern="^(Team_Members|Ambassadors|All)$"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Task Deadline Policy",
                "content": "The new deadline policy has been updated to require 48 hours notice instead of 24 hours."
            }
        }


class AnnouncementResponse(BaseModel):
    """Announcement response schema"""
    id: uuid.UUID = Field(..., description="Announcement unique identifier")
    title: str = Field(..., description="Announcement title")
    content: str = Field(..., description="Announcement content")
    target_group: str = Field(..., description="Target group (Team_Members, Ambassadors, or All)")
    created_by_id: uuid.UUID = Field(..., description="ID of the admin who created the announcement")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "New Task Deadline Policy",
                "content": "Starting next month, all tasks must be submitted at least 24 hours before the deadline.",
                "target_group": "All",
                "created_by_id": "223e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        }


class AnnouncementListResponse(BaseModel):
    """Announcement list response schema"""
    announcements: List[AnnouncementResponse] = Field(..., description="List of announcements")
    total: int = Field(..., description="Total number of announcements", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Number of items per page", ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "announcements": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "New Task Deadline Policy",
                        "content": "Starting next month, all tasks must be submitted at least 24 hours before the deadline.",
                        "target_group": "All",
                        "created_by_id": "223e4567-e89b-12d3-a456-426614174001",
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T10:00:00Z"
                    }
                ],
                "total": 5,
                "page": 1,
                "page_size": 20
            }
        }


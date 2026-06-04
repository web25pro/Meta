"""Schedule schemas"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import List, Optional
import uuid


class ScheduleCreateRequest(BaseModel):
    """Schedule creation request schema"""
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: str = Field(..., min_length=1, description="Event description")
    event_date: datetime = Field(..., description="Date and time of the event")
    target_group: str = Field(
        ...,
        description="Target group (Team_Members, Ambassadors, or All)",
        pattern="^(Team_Members|Ambassadors|All)$"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Team Meeting",
                "description": "Monthly team sync meeting to discuss progress and upcoming tasks",
                "event_date": "2024-02-15T14:00:00Z",
                "target_group": "Team_Members"
            }
        }


class ScheduleUpdateRequest(BaseModel):
    """Schedule update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(None, min_length=1, description="Event description")
    event_date: Optional[datetime] = Field(None, description="Date and time of the event")
    target_group: Optional[str] = Field(
        None,
        description="Target group (Team_Members, Ambassadors, or All)",
        pattern="^(Team_Members|Ambassadors|All)$"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Team Meeting",
                "event_date": "2024-02-15T15:00:00Z"
            }
        }


class ScheduleResponse(BaseModel):
    """Schedule response schema"""
    id: uuid.UUID = Field(..., description="Schedule unique identifier")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    event_date: datetime = Field(..., description="Date and time of the event")
    target_group: str = Field(..., description="Target group (Team_Members, Ambassadors, or All)")
    created_by_id: uuid.UUID = Field(..., description="ID of the admin who created the schedule")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Team Meeting",
                "description": "Monthly team sync meeting",
                "event_date": "2024-02-15T14:00:00Z",
                "target_group": "Team_Members",
                "created_by_id": "223e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        }


class ScheduleListResponse(BaseModel):
    """Schedule list response schema"""
    schedules: List[ScheduleResponse] = Field(..., description="List of schedule events")
    total: int = Field(..., description="Total number of schedules", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(..., description="Number of items per page", ge=1, le=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "schedules": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "title": "Team Meeting",
                        "description": "Monthly team sync meeting",
                        "event_date": "2024-02-15T14:00:00Z",
                        "target_group": "Team_Members",
                        "created_by_id": "223e4567-e89b-12d3-a456-426614174001",
                        "created_at": "2024-01-15T10:00:00Z",
                        "updated_at": "2024-01-15T10:00:00Z"
                    }
                ],
                "total": 10,
                "page": 1,
                "page_size": 20
            }
        }


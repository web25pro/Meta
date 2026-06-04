"""Task schemas"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.models import AssignedGroup


class TaskBase(BaseModel):
    """Base task schema with common fields"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Task title",
        examples=["Complete project documentation"]
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed task description",
        examples=["Write comprehensive documentation for the API endpoints including examples and error codes"]
    )
    assigned_to_group: AssignedGroup = Field(
        ...,
        description="Target group for task assignment (Team_Members, Ambassadors, or All)",
        examples=["Team_Members"]
    )
    deadline: datetime = Field(
        ...,
        description="Task deadline (ISO 8601 format). Missing this deadline results in 100 PP penalty.",
        examples=["2024-02-15T23:59:59Z"]
    )
    point_value: float = Field(
        ...,
        ge=0,
        description="Points awarded upon task completion (Team_Members: 50 PP, Ambassadors: 138.6 PP)",
        examples=[50.0]
    )
    
    @field_validator('deadline')
    @classmethod
    def validate_deadline_in_future(cls, v: datetime) -> datetime:
        """
        Validate that deadline is in the future.
        
        Args:
            v: Deadline datetime value
            
        Returns:
            datetime: Validated deadline
            
        Raises:
            ValueError: If deadline is in the past
        """
        # Make deadline timezone-aware if it's naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError('Deadline must be in the future')
        
        return v
    
    @field_validator('point_value')
    @classmethod
    def validate_point_value(cls, v: float) -> float:
        """
        Validate that point value is reasonable.
        
        Args:
            v: Point value
            
        Returns:
            float: Validated point value
            
        Raises:
            ValueError: If point value is unreasonable
        """
        if v > 10000:
            raise ValueError('Point value cannot exceed 10,000 PP')
        
        return v


class TaskCreate(TaskBase):
    """
    Task creation schema for admin operations.
    
    Overall_Admin can assign to any group. Ambassador_Admin can only assign to Ambassadors.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Complete project documentation",
                    "description": "Write comprehensive documentation for the API endpoints",
                    "assigned_to_group": "Team_Members",
                    "deadline": "2024-02-15T23:59:59Z",
                    "point_value": 50.0
                }
            ]
        }
    )


class TaskUpdate(BaseModel):
    """
    Task update schema for modifying existing tasks.
    
    All fields are optional. Only provided fields will be updated.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Updated task title",
                    "description": "Updated task description",
                    "deadline": "2024-02-20T23:59:59Z",
                    "point_value": 75.0
                }
            ]
        }
    )
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Task title",
        examples=["Updated task title"]
    )
    description: Optional[str] = Field(
        None,
        min_length=1,
        description="Task description",
        examples=["Updated task description"]
    )
    assigned_to_group: Optional[AssignedGroup] = Field(
        None,
        description="Target group for task assignment",
        examples=["Ambassadors"]
    )
    deadline: Optional[datetime] = Field(
        None,
        description="Task deadline",
        examples=["2024-02-20T23:59:59Z"]
    )
    point_value: Optional[float] = Field(
        None,
        ge=0,
        description="Points awarded upon completion",
        examples=[75.0]
    )
    
    @field_validator('deadline')
    @classmethod
    def validate_deadline_in_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        """
        Validate that deadline is in the future.
        
        Args:
            v: Deadline datetime value
            
        Returns:
            Optional[datetime]: Validated deadline
            
        Raises:
            ValueError: If deadline is in the past
        """
        if v is None:
            return v
        
        # Make deadline timezone-aware if it's naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError('Deadline must be in the future')
        
        return v
    
    @field_validator('point_value')
    @classmethod
    def validate_point_value(cls, v: Optional[float]) -> Optional[float]:
        """
        Validate that point value is reasonable.
        
        Args:
            v: Point value
            
        Returns:
            Optional[float]: Validated point value
            
        Raises:
            ValueError: If point value is unreasonable
        """
        if v is not None and v > 10000:
            raise ValueError('Point value cannot exceed 10,000 PP')
        
        return v


class TaskResponse(TaskBase):
    """
    Task response schema with full task information.
    
    Includes task ID, creator information, and timestamps.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Complete project documentation",
                    "description": "Write comprehensive documentation for the API endpoints",
                    "assigned_to_group": "Team_Members",
                    "deadline": "2024-02-15T23:59:59Z",
                    "point_value": 50.0,
                    "created_by_id": "987e6543-e21b-12d3-a456-426614174000",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    )
    
    id: uuid.UUID = Field(
        ...,
        description="Unique task identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    created_by_id: uuid.UUID = Field(
        ...,
        description="ID of the admin who created the task",
        examples=["987e6543-e21b-12d3-a456-426614174000"]
    )
    created_at: datetime = Field(
        ...,
        description="Task creation timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )


class TaskListResponse(BaseModel):
    """
    Paginated task list response.
    
    Contains list of tasks and pagination metadata.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tasks": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "title": "Complete project documentation",
                            "description": "Write comprehensive documentation",
                            "assigned_to_group": "Team_Members",
                            "deadline": "2024-02-15T23:59:59Z",
                            "point_value": 50.0,
                            "created_by_id": "987e6543-e21b-12d3-a456-426614174000",
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "total": 25,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    )
    
    tasks: list[TaskResponse] = Field(
        ...,
        description="List of tasks for current page"
    )
    total: int = Field(
        ...,
        description="Total number of tasks",
        ge=0,
        examples=[25]
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        ge=1,
        examples=[1]
    )
    page_size: int = Field(
        ...,
        description="Number of tasks per page",
        ge=1,
        le=100,
        examples=[20]
    )

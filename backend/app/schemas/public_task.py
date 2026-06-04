"""Pydantic schemas for public task operations"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class TaskCategory(str, Enum):
    """Public task category enumeration"""
    SOCIAL_MEDIA = "Social_Media"
    CONTENT_CREATION = "Content_Creation"
    COMMUNITY_ENGAGEMENT = "Community_Engagement"
    SURVEYS = "Surveys"
    REFERRALS = "Referrals"


class DifficultyLevel(str, Enum):
    """Task difficulty level enumeration"""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class PublicTaskSummary(BaseModel):
    """Schema for public task in list view"""
    id: UUID
    title: str
    description: str
    point_value: float
    deadline: datetime
    category: Optional[TaskCategory]
    difficulty_level: Optional[DifficultyLevel]
    estimated_time_minutes: Optional[int]
    featured: bool
    current_submissions: int
    max_submissions: Optional[int]
    
    model_config = {"from_attributes": True}


class PublicTaskDetail(BaseModel):
    """Schema for detailed public task view"""
    id: UUID
    title: str
    description: str
    point_value: float
    deadline: datetime
    category: Optional[TaskCategory]
    difficulty_level: Optional[DifficultyLevel]
    estimated_time_minutes: Optional[int]
    featured: bool
    current_submissions: int
    max_submissions: Optional[int]
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PaginatedTaskResponse(BaseModel):
    """Schema for paginated task list response"""
    tasks: List[PublicTaskSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskSubmissionRequest(BaseModel):
    """Schema for task submission request"""
    content: str = Field(..., min_length=10, description="Submission content/proof")
    # Note: Files will be handled separately via FastAPI's UploadFile


class TaskSubmissionResponse(BaseModel):
    """Schema for task submission response"""
    id: UUID
    task_id: UUID
    user_id: UUID
    content: str
    status: str
    submitted_at: datetime
    
    model_config = {"from_attributes": True}


class TaskSubmissionDetail(BaseModel):
    """Schema for detailed submission view"""
    id: UUID
    task_id: UUID
    task_title: str
    content: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    reviewer_feedback: Optional[str]
    file_urls: List[str]
    
    model_config = {"from_attributes": True}


class UserSubmissionsResponse(BaseModel):
    """Schema for user's submission list"""
    submissions: List[TaskSubmissionDetail]
    total: int
    page: int
    page_size: int

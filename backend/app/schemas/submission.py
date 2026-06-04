"""Submission schemas"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
import uuid

from app.models import SubmissionStatus


class SubmissionFileData(BaseModel):
    """
    File data for submission upload.
    
    Used when submitting files with a task submission.
    """
    file_name: str = Field(
        ...,
        description="Original filename",
        examples=["report.pdf"]
    )
    file_data: bytes = Field(
        ...,
        description="Binary file content"
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file",
        examples=["application/pdf"]
    )


class SubmissionCreate(BaseModel):
    """
    Submission creation schema for task completion.
    
    Users can submit text content and optionally attach files.
    Only one submission per task per user is allowed.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "123e4567-e89b-12d3-a456-426614174000",
                    "content": "I have completed the task. Here are the results...",
                    "files": None
                }
            ]
        }
    )
    
    task_id: uuid.UUID = Field(
        ...,
        description="ID of the task being submitted",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Submission content (text, links, or description)",
        examples=["I have completed the task. Here are the results and documentation links..."]
    )
    files: Optional[List[SubmissionFileData]] = Field(
        None,
        description="Optional list of files to attach (max 50MB per file, 200MB total)"
    )


class SubmissionUpdate(BaseModel):
    """
    Submission update schema for modifying submission content.
    
    Only content can be updated. Files cannot be modified after submission.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content": "Updated submission content with additional details..."
                }
            ]
        }
    )
    
    content: Optional[str] = Field(
        None,
        min_length=1,
        description="Updated submission content",
        examples=["Updated submission content with additional details..."]
    )


class SubmissionFileResponse(BaseModel):
    """
    Submission file response schema.
    
    Contains file metadata and scan status.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "456e7890-e12b-34d5-a678-426614174000",
                    "file_name": "report.pdf",
                    "file_size": 1048576,
                    "mime_type": "application/pdf",
                    "scan_status": "clean",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    )
    
    id: uuid.UUID = Field(
        ...,
        description="Unique file identifier",
        examples=["456e7890-e12b-34d5-a678-426614174000"]
    )
    file_name: str = Field(
        ...,
        description="Original filename",
        examples=["report.pdf"]
    )
    file_size: int = Field(
        ...,
        description="File size in bytes",
        examples=[1048576]
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file",
        examples=["application/pdf"]
    )
    scan_status: str = Field(
        ...,
        description="Virus scan status (pending, clean, infected)",
        examples=["clean"]
    )
    created_at: datetime = Field(
        ...,
        description="File upload timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )


class SubmissionResponse(BaseModel):
    """
    Submission response schema with full submission information.
    
    Includes submission content, status, review information, and attached files.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "789e0123-e45b-67d8-a901-426614174000",
                    "task_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "234e5678-e90b-12d3-a456-426614174000",
                    "content": "Task completed successfully with all requirements met",
                    "status": "Approved",
                    "submitted_at": "2024-01-15T10:30:00Z",
                    "reviewed_by_id": "345e6789-e01b-23d4-a567-426614174000",
                    "reviewed_at": "2024-01-16T14:20:00Z",
                    "files": []
                }
            ]
        }
    )
    
    id: uuid.UUID = Field(
        ...,
        description="Unique submission identifier",
        examples=["789e0123-e45b-67d8-a901-426614174000"]
    )
    task_id: uuid.UUID = Field(
        ...,
        description="ID of the submitted task",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user who submitted",
        examples=["234e5678-e90b-12d3-a456-426614174000"]
    )
    content: str = Field(
        ...,
        description="Submission content",
        examples=["Task completed successfully with all requirements met"]
    )
    status: SubmissionStatus = Field(
        ...,
        description="Submission status (Pending, Approved, Rejected)",
        examples=["Approved"]
    )
    submitted_at: datetime = Field(
        ...,
        description="Submission timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    reviewed_by_id: Optional[uuid.UUID] = Field(
        None,
        description="ID of the admin who reviewed the submission",
        examples=["345e6789-e01b-23d4-a567-426614174000"]
    )
    reviewed_at: Optional[datetime] = Field(
        None,
        description="Review timestamp",
        examples=["2024-01-16T14:20:00Z"]
    )
    files: List[SubmissionFileResponse] = Field(
        default=[],
        description="List of attached files"
    )


class SubmissionListResponse(BaseModel):
    """
    Paginated submission list response.
    
    Contains list of submissions and pagination metadata.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "submissions": [
                        {
                            "id": "789e0123-e45b-67d8-a901-426614174000",
                            "task_id": "123e4567-e89b-12d3-a456-426614174000",
                            "user_id": "234e5678-e90b-12d3-a456-426614174000",
                            "content": "Task completed",
                            "status": "Approved",
                            "submitted_at": "2024-01-15T10:30:00Z",
                            "reviewed_by_id": "345e6789-e01b-23d4-a567-426614174000",
                            "reviewed_at": "2024-01-16T14:20:00Z",
                            "files": []
                        }
                    ],
                    "total": 15,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    )
    
    submissions: List[SubmissionResponse] = Field(
        ...,
        description="List of submissions for current page"
    )
    total: int = Field(
        ...,
        description="Total number of submissions",
        ge=0,
        examples=[15]
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        ge=1,
        examples=[1]
    )
    page_size: int = Field(
        ...,
        description="Number of submissions per page",
        ge=1,
        le=100,
        examples=[20]
    )


class SubmissionReviewRequest(BaseModel):
    """
    Submission review request for admin approval/rejection.
    
    Approving a submission awards points to the user (50 PP for Team_Members, 138.6 PP for Ambassadors).
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "approved": True
                }
            ]
        }
    )
    
    approved: bool = Field(
        ...,
        description="True to approve submission (awards points), False to reject",
        examples=[True]
    )

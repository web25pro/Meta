"""Service for public task operations"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile
import json

from app.models.task import Task
from app.models.submission import TaskSubmission, SubmissionStatus, SubmissionFile
from app.models.user import User
from app.schemas.public_task import TaskCategory
from app.core.config import settings


async def get_public_tasks(
    db: AsyncSession,
    category: Optional[TaskCategory] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[Task], int]:
    """
    Get paginated list of public tasks.
    
    Args:
        db: Database session
        category: Optional category filter
        page: Page number (1-indexed)
        page_size: Number of tasks per page
        
    Returns:
        Tuple of (tasks list, total count)
    """
    # Build query
    query = select(Task).where(
        and_(
            Task.is_public == True,
            Task.is_active == True,
            Task.deleted_at.is_(None),
            Task.deadline > datetime.utcnow()
        )
    )
    
    # Apply category filter if provided
    if category:
        query = query.where(Task.category == category)
    
    # Order by featured first, then deadline
    query = query.order_by(Task.featured.desc(), Task.deadline.asc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar_one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return list(tasks), total


async def get_task_by_id(db: AsyncSession, task_id: UUID) -> Optional[Task]:
    """
    Get task by ID.
    
    Args:
        db: Database session
        task_id: Task UUID
        
    Returns:
        Task object if found and public, None otherwise
    """
    result = await db.execute(
        select(Task).where(
            and_(
                Task.id == task_id,
                Task.is_public == True,
                Task.deleted_at.is_(None)
            )
        )
    )
    return result.scalar_one_or_none()


async def check_user_already_submitted(
    db: AsyncSession,
    user_id: UUID,
    task_id: UUID
) -> bool:
    """
    Check if user has already submitted to this task.
    
    Args:
        db: Database session
        user_id: User UUID
        task_id: Task UUID
        
    Returns:
        True if user has already submitted, False otherwise
    """
    result = await db.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.user_id == user_id,
                TaskSubmission.task_id == task_id
            )
        )
    )
    existing_submission = result.scalar_one_or_none()
    return existing_submission is not None


async def create_task_submission(
    db: AsyncSession,
    user_id: UUID,
    task_id: UUID,
    content: str,
    file_urls: List[str] = []
) -> TaskSubmission:
    """
    Create a new task submission.
    
    Args:
        db: Database session
        user_id: User UUID
        task_id: Task UUID
        content: Submission content/proof
        file_urls: List of uploaded file URLs
        
    Returns:
        Created TaskSubmission object
        
    Raises:
        HTTPException: If validation fails
    """
    # Get task
    task = await get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TASK_NOT_FOUND"
        )
    
    # Check if task is active
    if not task.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TASK_NOT_ACTIVE"
        )
    
    # Check deadline
    if task.deadline < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DEADLINE_PASSED"
        )
    
    # Check if user already submitted
    if await check_user_already_submitted(db, user_id, task_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DUPLICATE_SUBMISSION"
        )
    
    # Check max submissions limit
    if task.max_submissions and task.current_submissions >= task.max_submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SUBMISSION_LIMIT_REACHED"
        )
    
    # Get user to check email verification
    user = await db.get(User, user_id)
    if not user or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMAIL_NOT_VERIFIED"
        )
    
    # Create submission
    submission = TaskSubmission(
        task_id=task_id,
        user_id=user_id,
        content=content,
        status=SubmissionStatus.PENDING
    )
    
    db.add(submission)
    await db.flush()  # Flush to get submission ID
    
    # Create submission files if any
    for file_url in file_urls:
        submission_file = SubmissionFile(
            submission_id=submission.id,
            file_url=file_url,
            file_name=file_url.split('/')[-1]  # Extract filename from URL
        )
        db.add(submission_file)
    
    # Increment task submission counter
    task.current_submissions += 1
    
    await db.commit()
    await db.refresh(submission)
    
    return submission


async def get_user_submissions(
    db: AsyncSession,
    user_id: UUID,
    status_filter: Optional[SubmissionStatus] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[TaskSubmission], int]:
    """
    Get user's task submissions with optional status filter.
    
    Args:
        db: Database session
        user_id: User UUID
        status_filter: Optional status filter
        page: Page number (1-indexed)
        page_size: Number of submissions per page
        
    Returns:
        Tuple of (submissions list, total count)
    """
    # Build query
    query = select(TaskSubmission).where(TaskSubmission.user_id == user_id)
    
    # Apply status filter if provided
    if status_filter:
        query = query.where(TaskSubmission.status == status_filter)
    
    # Order by submission date descending
    query = query.order_by(TaskSubmission.submitted_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar_one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    return list(submissions), total


async def upload_file_to_s3(file: UploadFile) -> str:
    """
    Upload file to S3 and return URL.
    
    Args:
        file: Uploaded file
        
    Returns:
        S3 file URL
        
    Note: This is a placeholder. Actual S3 upload logic should be implemented.
    """
    # Try to use the configured S3 client to generate a presigned upload URL.
    # If S3 is not initialized or unavailable, fall back to a placeholder URL.
    filename = file.filename or "upload"
    try:
        # Local import to avoid forcing boto3 requirement at module import time
        from app.core.s3 import generate_presigned_url, get_s3_client
        import uuid

        # Ensure client is initialized (get_s3_client will raise if not)
        _ = get_s3_client()

        key = f"submissions/{uuid.uuid4()}_{filename}"
        # Generate a presigned PUT URL so callers can upload directly
        url = generate_presigned_url(key=key, http_method="PUT")
        return url
    except Exception:
        # Fallback placeholder URL when S3 isn't configured in the environment
        return f"https://s3.amazonaws.com/{settings.S3_BUCKET_NAME}/{filename}"


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file.
    
    Args:
        file: Uploaded file
        
    Raises:
        HTTPException: If file validation fails
    """
    # Check file size (10MB max)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    # Check file type (images, PDFs, documents only)
    ALLOWED_EXTENSIONS = {
        'jpg', 'jpeg', 'png', 'gif', 'pdf', 
        'doc', 'docx', 'txt', 'mp4', 'mov'
    }
    
    if file.filename:
        extension = file.filename.split('.')[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"FILE_TYPE_NOT_ALLOWED: Allowed types are {', '.join(ALLOWED_EXTENSIONS)}"
            )
    
    # Note: File size check would be done during upload
    # This is a placeholder for the validation logic

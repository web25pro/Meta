"""Submission API endpoints"""
import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models import User, UserRole
from app.services.submission_service import SubmissionService
from app.schemas.submission import (
    SubmissionCreate, 
    SubmissionResponse, 
    SubmissionListResponse,
    SubmissionReviewRequest
)
from app.api.user import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(
    submission_data: SubmissionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create a new task submission.
    
    Users can submit text and optionally attach files.
    Only one submission per task per user is allowed.
    Deadline enforcement is checked in the service layer.
    """
    try:
        submission = await SubmissionService.create_submission(
            db=db,
            submission_data=submission_data,
            user_id=current_user.id
        )
        return submission
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-submissions", response_model=SubmissionListResponse)
async def get_my_submissions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get submissions for the current user.
    """
    submissions, total = await SubmissionService.get_user_submissions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return {
        "submissions": submissions,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get submission details by ID.
    """
    submission = await SubmissionService.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    
    # Non-admins can only see their own submissions
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        if submission.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            
    return submission


@router.get("/task/{task_id}", response_model=SubmissionListResponse)
async def list_task_submissions(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List all submissions for a specific task (Admin only).
    """
    try:
        submissions, total = await SubmissionService.list_submissions_for_task(
            db=db,
            task_id=task_id,
            admin_role=current_user.role,
            page=page,
            page_size=page_size
        )
        
        return {
            "submissions": submissions,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{submission_id}/review", response_model=SubmissionResponse)
async def review_submission(
    submission_id: uuid.UUID,
    review_data: SubmissionReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Review a submission (Approve or Reject).
    
    Approving a submission awards points to the user.
    """
    try:
        if review_data.approved:
            submission = await SubmissionService.approve_submission(
                db=db,
                submission_id=submission_id,
                admin_id=current_user.id,
                admin_role=current_user.role
            )
        else:
            submission = await SubmissionService.reject_submission(
                db=db,
                submission_id=submission_id,
                admin_id=current_user.id,
                admin_role=current_user.role
            )
        return submission
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

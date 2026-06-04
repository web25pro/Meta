"""Submission service layer"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models import (
    TaskSubmission, SubmissionFile, Task, User, UserRole, 
    SubmissionStatus, FileScanStatus
)
from app.core.rbac import Permission, has_permission
from app.schemas.submission import SubmissionCreate, SubmissionFileData


class SubmissionService:
    """Submission service for business logic"""
    
    @staticmethod
    async def create_submission(
        db: AsyncSession,
        submission_data: SubmissionCreate,
        user_id: uuid.UUID
    ) -> TaskSubmission:
        """
        Create a new submission.
        
        Args:
            db: Database session
            submission_data: Submission creation data
            user_id: ID of the user creating the submission
            
        Returns:
            TaskSubmission: Created submission
            
        Raises:
            ValueError: If task not found, deadline passed, or duplicate submission
        """
        # Get task
        result = await db.execute(
            select(Task).where(Task.id == submission_data.task_id, Task.deleted_at.is_(None))
        )
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError(f"Task with ID {submission_data.task_id} not found")
        
        # Check if deadline has passed
        if task.deadline < datetime.utcnow():
            raise ValueError("Cannot submit task after deadline has passed")
        
        # Check if user already submitted for this task
        result = await db.execute(
            select(TaskSubmission).where(
                TaskSubmission.task_id == submission_data.task_id,
                TaskSubmission.user_id == user_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("User has already submitted for this task")
        
        # Validate file sizes
        if submission_data.files:
            total_size = sum(len(f.file_data) for f in submission_data.files)
            max_submission_size = 200 * 1024 * 1024  # 200MB
            if total_size > max_submission_size:
                raise ValueError(f"Total file size exceeds maximum of 200MB")
            
            for file in submission_data.files:
                max_file_size = 50 * 1024 * 1024  # 50MB
                if len(file.file_data) > max_file_size:
                    raise ValueError(f"File {file.file_name} exceeds maximum size of 50MB")
        
        # Create submission
        submission = TaskSubmission(
            task_id=submission_data.task_id,
            user_id=user_id,
            content=submission_data.content,
            status=SubmissionStatus.PENDING
        )
        
        db.add(submission)
        await db.flush()  # Get submission ID
        
        # Create file records
        if submission_data.files:
            for file_data in submission_data.files:
                file_record = SubmissionFile(
                    submission_id=submission.id,
                    file_name=file_data.file_name,
                    file_size=len(file_data.file_data),
                    file_data=file_data.file_data,
                    mime_type=file_data.mime_type,
                    scan_status=FileScanStatus.PENDING
                )
                db.add(file_record)
        
        await db.commit()
        await db.refresh(submission)
        
        return submission
    
    @staticmethod
    async def get_submission_by_id(
        db: AsyncSession,
        submission_id: uuid.UUID
    ) -> Optional[TaskSubmission]:
        """
        Get submission by ID.
        
        Args:
            db: Database session
            submission_id: Submission ID
            
        Returns:
            TaskSubmission: Submission or None if not found
        """
        result = await db.execute(
            select(TaskSubmission).where(TaskSubmission.id == submission_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_submissions_for_task(
        db: AsyncSession,
        task_id: uuid.UUID,
        admin_role: UserRole,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[TaskSubmission], int]:
        """
        List submissions for a task (admin only).
        
        Args:
            db: Database session
            task_id: Task ID
            admin_role: Role of the admin listing submissions
            page: Page number (1-indexed)
            page_size: Number of submissions per page
            
        Returns:
            tuple: (list of submissions, total count)
            
        Raises:
            PermissionError: If user is not an admin
        """
        # Check if user has permission
        if not has_permission(admin_role, Permission.APPROVE_SUBMISSION):
            raise PermissionError(f"Role {admin_role} does not have permission to view submissions")
        
        # Build query
        query = select(TaskSubmission).where(TaskSubmission.task_id == task_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(TaskSubmission.submitted_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        return list(submissions), total
    
    @staticmethod
    async def get_user_submissions(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[TaskSubmission], int]:
        """
        Get submissions for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of submissions per page
            
        Returns:
            tuple: (list of submissions, total count)
        """
        # Build query
        query = select(TaskSubmission).where(TaskSubmission.user_id == user_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(TaskSubmission.submitted_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        submissions = result.scalars().all()
        
        return list(submissions), total
    
    @staticmethod
    async def approve_submission(
        db: AsyncSession,
        submission_id: uuid.UUID,
        admin_id: uuid.UUID,
        admin_role: UserRole
    ) -> TaskSubmission:
        """
        Approve a submission.
        
        Args:
            db: Database session
            submission_id: Submission ID
            admin_id: ID of the admin approving
            admin_role: Role of the admin approving
            
        Returns:
            TaskSubmission: Updated submission
            
        Raises:
            PermissionError: If admin cannot approve submissions
            ValueError: If submission not found or already reviewed
        """
        # Check if admin has permission
        if not has_permission(admin_role, Permission.APPROVE_SUBMISSION):
            raise PermissionError(f"Role {admin_role} does not have permission to approve submissions")
        
        # Get submission
        submission = await SubmissionService.get_submission_by_id(db, submission_id)
        if not submission:
            raise ValueError(f"Submission with ID {submission_id} not found")
        
        # Check if already reviewed
        if submission.status != SubmissionStatus.PENDING:
            raise ValueError(f"Submission has already been reviewed with status {submission.status}")
        
        # Update submission
        submission.status = SubmissionStatus.APPROVED
        submission.reviewed_by_id = admin_id
        submission.reviewed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(submission)
        
        return submission
    
    @staticmethod
    async def reject_submission(
        db: AsyncSession,
        submission_id: uuid.UUID,
        admin_id: uuid.UUID,
        admin_role: UserRole
    ) -> TaskSubmission:
        """
        Reject a submission.
        
        Args:
            db: Database session
            submission_id: Submission ID
            admin_id: ID of the admin rejecting
            admin_role: Role of the admin rejecting
            
        Returns:
            TaskSubmission: Updated submission
            
        Raises:
            PermissionError: If admin cannot reject submissions
            ValueError: If submission not found or already reviewed
        """
        # Check if admin has permission
        if not has_permission(admin_role, Permission.REJECT_SUBMISSION):
            raise PermissionError(f"Role {admin_role} does not have permission to reject submissions")
        
        # Get submission
        submission = await SubmissionService.get_submission_by_id(db, submission_id)
        if not submission:
            raise ValueError(f"Submission with ID {submission_id} not found")
        
        # Check if already reviewed
        if submission.status != SubmissionStatus.PENDING:
            raise ValueError(f"Submission has already been reviewed with status {submission.status}")
        
        # Update submission
        submission.status = SubmissionStatus.REJECTED
        submission.reviewed_by_id = admin_id
        submission.reviewed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(submission)
        
        return submission
    
    @staticmethod
    async def get_submission_file(
        db: AsyncSession,
        file_id: uuid.UUID
    ) -> Optional[SubmissionFile]:
        """
        Get submission file by ID.
        
        Args:
            db: Database session
            file_id: File ID
            
        Returns:
            SubmissionFile: File or None if not found
        """
        result = await db.execute(
            select(SubmissionFile).where(SubmissionFile.id == file_id)
        )
        return result.scalar_one_or_none()

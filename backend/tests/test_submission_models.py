"""Tests for submission models"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, UserRole, UserType, Task, AssignedGroup,
    TaskSubmission, SubmissionFile, SubmissionStatus, FileScanStatus
)


@pytest.mark.unit
class TestTaskSubmissionModel:
    """Test TaskSubmission model"""
    
    async def test_create_submission(self, db_session: AsyncSession):
        """Test creating a task submission"""
        # Create admin user
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.OVERALL_ADMIN,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(admin)
        
        # Create regular user
        user = User(
            name="Regular User",
            email="user@example.com",
            password_hash="hashed_password",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(user)
        
        # Create a task
        task = Task(
            title="Test Task",
            description="This is a test task",
            assigned_to_group=AssignedGroup.TEAM_MEMBERS,
            deadline=datetime.utcnow() + timedelta(days=7),
            point_value=50.0,
            created_by_id=admin.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        # Create a submission
        submission = TaskSubmission(
            task_id=task.id,
            user_id=user.id,
            content="This is my submission content"
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)
        
        assert submission.id is not None
        assert submission.task_id == task.id
        assert submission.user_id == user.id
        assert submission.status == SubmissionStatus.PENDING


@pytest.mark.unit
class TestSubmissionFileModel:
    """Test SubmissionFile model"""
    
    async def test_create_submission_file(self, db_session: AsyncSession):
        """Test creating a submission file"""
        # Create users
        admin = User(
            name="Admin User",
            email="admin4@example.com",
            password_hash="hashed_password",
            role=UserRole.OVERALL_ADMIN,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(admin)
        
        user = User(
            name="Regular User",
            email="user4@example.com",
            password_hash="hashed_password",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(admin)
        await db_session.refresh(user)
        
        # Create a task
        task = Task(
            title="Test Task",
            description="This is a test task",
            assigned_to_group=AssignedGroup.TEAM_MEMBERS,
            deadline=datetime.utcnow() + timedelta(days=7),
            point_value=50.0,
            created_by_id=admin.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        # Create a submission
        submission = TaskSubmission(
            task_id=task.id,
            user_id=user.id,
            content="This is my submission content"
        )
        db_session.add(submission)
        await db_session.commit()
        await db_session.refresh(submission)
        
        # Create a submission file
        file = SubmissionFile(
            submission_id=submission.id,
            file_name="test.pdf",
            file_size=1024,
            s3_key="submissions/test-id/test.pdf",
            mime_type="application/pdf"
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)
        
        assert file.id is not None
        assert file.submission_id == submission.id
        assert file.file_name == "test.pdf"
        assert file.scan_status == FileScanStatus.PENDING

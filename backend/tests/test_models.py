"""Tests for database models"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserType, Task, TaskAssignment, AssignedGroup


@pytest.mark.unit
class TestUserModel:
    """Test User model"""
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user"""
        user = User(
            name="Test User",
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.TEAM_MEMBER,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.role == UserRole.TEAM_MEMBER
        assert user.user_type == UserType.TEAM_MEMBER
        assert user.points == 0.0
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.deleted_at is None


@pytest.mark.unit
class TestTaskModel:
    """Test Task model"""
    
    async def test_create_task(self, db_session: AsyncSession):
        """Test creating a task"""
        # Create a user first (required for foreign key)
        user = User(
            name="Admin User",
            email="admin@example.com",
            password_hash="hashed_password",
            role=UserRole.OVERALL_ADMIN,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a task
        deadline = datetime.utcnow() + timedelta(days=7)
        task = Task(
            title="Test Task",
            description="This is a test task",
            assigned_to_group=AssignedGroup.TEAM_MEMBERS,
            deadline=deadline,
            point_value=50.0,
            created_by_id=user.id
        )
        
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "This is a test task"
        assert task.assigned_to_group == AssignedGroup.TEAM_MEMBERS
        assert task.deadline == deadline
        assert task.point_value == 50.0
        assert task.created_by_id == user.id
        assert task.created_at is not None
        assert task.updated_at is not None
        assert task.deleted_at is None
    
    async def test_task_creator_relationship(self, db_session: AsyncSession):
        """Test task creator relationship"""
        # Create a user
        user = User(
            name="Admin User",
            email="admin2@example.com",
            password_hash="hashed_password",
            role=UserRole.OVERALL_ADMIN,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Create a task
        task = Task(
            title="Test Task",
            description="This is a test task",
            assigned_to_group=AssignedGroup.TEAM_MEMBERS,
            deadline=datetime.utcnow() + timedelta(days=7),
            point_value=50.0,
            created_by_id=user.id
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)
        
        # Load the task with creator relationship
        result = await db_session.execute(
            select(Task).where(Task.id == task.id)
        )
        loaded_task = result.scalar_one()
        
        # Access the creator relationship
        await db_session.refresh(loaded_task, ["creator"])
        assert loaded_task.creator.id == user.id
        assert loaded_task.creator.name == "Admin User"


@pytest.mark.unit
class TestTaskAssignmentModel:
    """Test TaskAssignment model"""
    
    async def test_create_task_assignment(self, db_session: AsyncSession):
        """Test creating a task assignment"""
        # Create admin user
        admin = User(
            name="Admin User",
            email="admin3@example.com",
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
        
        # Create task assignment
        assignment = TaskAssignment(
            task_id=task.id,
            user_id=user.id
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)
        
        assert assignment.id is not None
        assert assignment.task_id == task.id
        assert assignment.user_id == user.id
        assert assignment.assigned_at is not None
    
    async def test_task_assignment_relationships(self, db_session: AsyncSession):
        """Test task assignment relationships"""
        # Create admin user
        admin = User(
            name="Admin User",
            email="admin4@example.com",
            password_hash="hashed_password",
            role=UserRole.OVERALL_ADMIN,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(admin)
        
        # Create regular user
        user = User(
            name="Regular User",
            email="user2@example.com",
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
        
        # Create task assignment
        assignment = TaskAssignment(
            task_id=task.id,
            user_id=user.id
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)
        
        # Load assignment with relationships
        result = await db_session.execute(
            select(TaskAssignment).where(TaskAssignment.id == assignment.id)
        )
        loaded_assignment = result.scalar_one()
        
        # Access relationships
        await db_session.refresh(loaded_assignment, ["task", "user"])
        assert loaded_assignment.task.id == task.id
        assert loaded_assignment.task.title == "Test Task"
        assert loaded_assignment.user.id == user.id
        assert loaded_assignment.user.name == "Regular User"
    
    async def test_unique_task_user_assignment(self, db_session: AsyncSession):
        """Test that task-user assignment is unique"""
        # Create admin user
        admin = User(
            name="Admin User",
            email="admin5@example.com",
            password_hash="hashed_password",
            role=UserRole.OVERALL_ADMIN,
            user_type=UserType.TEAM_MEMBER,
            points=0.0
        )
        db_session.add(admin)
        
        # Create regular user
        user = User(
            name="Regular User",
            email="user3@example.com",
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
        
        # Create first assignment
        assignment1 = TaskAssignment(
            task_id=task.id,
            user_id=user.id
        )
        db_session.add(assignment1)
        await db_session.commit()
        
        # Try to create duplicate assignment
        assignment2 = TaskAssignment(
            task_id=task.id,
            user_id=user.id
        )
        db_session.add(assignment2)
        
        # Should raise an integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await db_session.commit()

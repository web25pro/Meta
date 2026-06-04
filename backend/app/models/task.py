"""Task and TaskAssignment models for task management"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssignedGroup(str, Enum):
    """Task assignment group enumeration"""
    TEAM_MEMBERS = "Team_Members"
    AMBASSADORS = "Ambassadors"
    ALL = "All"


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


class Task(Base):
    """
    Task model representing work items with deadlines and point values.
    
    Attributes:
        id: Unique identifier (UUID)
        title: Task title
        description: Detailed task description
        assigned_to_group: Target group for task assignment
        deadline: Task deadline timestamp
        point_value: Points awarded upon task completion
        created_by_id: ID of admin who created the task
        is_public: Flag to distinguish public tasks (for Community Users)
        category: Task category (for public tasks)
        max_submissions: Maximum number of submissions allowed (for public tasks)
        current_submissions: Current number of submissions (for public tasks)
        is_active: Whether task is active and accepting submissions
        featured: Whether task is featured in the feed
        difficulty_level: Task difficulty level (Easy, Medium, Hard)
        estimated_time_minutes: Estimated time to complete task
        created_at: Timestamp of task creation
        updated_at: Timestamp of last update
        deleted_at: Soft delete timestamp (NULL if not deleted)
    """
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_to_group: Mapped[AssignedGroup] = mapped_column(
        SQLEnum(AssignedGroup, name="assigned_group", create_type=True),
        nullable=False,
        index=True
    )
    deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    point_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Public task fields (nullable for backward compatibility)
    is_public: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        index=True
    )
    category: Mapped[TaskCategory | None] = mapped_column(
        SQLEnum(TaskCategory, name="task_category", create_type=True),
        nullable=True,
        index=True
    )
    max_submissions: Mapped[int | None] = mapped_column(
        nullable=True
    )
    current_submissions: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        index=True
    )
    featured: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )
    difficulty_level: Mapped[DifficultyLevel | None] = mapped_column(
        SQLEnum(DifficultyLevel, name="difficulty_level", create_type=True),
        nullable=True
    )
    estimated_time_minutes: Mapped[int | None] = mapped_column(
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[created_by_id]
    )
    task_assignments: Mapped[list["TaskAssignment"]] = relationship(
        "TaskAssignment",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    submissions: Mapped[list["TaskSubmission"]] = relationship(
        "TaskSubmission",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    submissions: Mapped[list["TaskSubmission"]] = relationship(
        "TaskSubmission",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, deadline={self.deadline})>"


class TaskAssignment(Base):
    """
    TaskAssignment model mapping tasks to individual users.
    
    Attributes:
        id: Unique identifier (UUID)
        task_id: ID of the assigned task
        user_id: ID of the assigned user
        assigned_at: Timestamp of assignment
    """
    __tablename__ = "task_assignments"
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_user_assignment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="task_assignments"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="task_assignments"
    )

    def __repr__(self) -> str:
        return f"<TaskAssignment(id={self.id}, task_id={self.task_id}, user_id={self.user_id})>"

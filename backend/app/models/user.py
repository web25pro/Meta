"""User model for authentication and role management"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Numeric, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    """User role enumeration"""
    OVERALL_ADMIN = "Overall_Admin"
    AMBASSADOR_ADMIN = "Ambassador_Admin"
    TEAM_MEMBER = "Team_Member"
    AMBASSADOR = "Ambassador"
    COMMUNITY_USER = "Community_User"  # New role for public users
    USER = "User"


class UserType(str, Enum):
    """User type enumeration"""
    TEAM_MEMBER = "Team_Member"
    AMBASSADOR = "Ambassador"
    COMMUNITY_USER = "Community_User"  # New type for public users
    USER = "User"


class User(Base):
    """
    User model representing platform users with role-based access control.
    
    Attributes:
        id: Unique identifier (UUID)
        name: User's full name
        email: User's email address (unique)
        password_hash: Bcrypt hashed password
        role: User's role (Overall_Admin, Ambassador_Admin, Team_Member, Ambassador)
        user_type: User's type (Team_Member or Ambassador)
        points: Current Panda Points (PP) balance
        created_at: Timestamp of user creation
        updated_at: Timestamp of last update
        deleted_at: Soft delete timestamp (NULL if not deleted)
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", create_type=True),
        nullable=False,
        index=True
    )
    user_type: Mapped[UserType] = mapped_column(
        SQLEnum(UserType, name="user_type", create_type=True),
        nullable=False,
        index=True
    )
    
    # Community User fields (optional for internal users)
    username: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )
    email_verified: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )
    email_verification_token: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    email_verification_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    referral_code: Mapped[str | None] = mapped_column(
        String(8),
        unique=True,
        nullable=True,
        index=True
    )
    referred_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    registration_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True
    )
    
    # Gamification fields
    points: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    xp: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
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
        default=None
    )

    # Relationships
    created_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="Task.created_by_id"
    )
    task_assignments: Mapped[list["TaskAssignment"]] = relationship(
        "TaskAssignment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    submissions: Mapped[list["TaskSubmission"]] = relationship(
        "TaskSubmission",
        back_populates="user",
        foreign_keys="TaskSubmission.user_id",
        cascade="all, delete-orphan"
    )
    reviewed_submissions: Mapped[list["TaskSubmission"]] = relationship(
        "TaskSubmission",
        back_populates="reviewer",
        foreign_keys="TaskSubmission.reviewed_by_id"
    )
    points_transactions: Mapped[list["PointsTransaction"]] = relationship(
        "PointsTransaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="admin_user",
        cascade="all, delete-orphan"
    )
    leaderboard_cache: Mapped["LeaderboardCache | None"] = relationship(
        "LeaderboardCache",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    created_schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    created_announcements: Mapped[list["Announcement"]] = relationship(
        "Announcement",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role}, type={self.user_type})>"

"""Leaderboard, schedule, and announcement models"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TargetGroup(str, Enum):
    """Target group enumeration for schedules and announcements"""
    TEAM_MEMBERS = "Team_Members"
    AMBASSADORS = "Ambassadors"
    ALL = "All"


class LeaderboardCache(Base):
    """
    LeaderboardCache model for fast leaderboard queries.
    
    Attributes:
        id: Unique identifier (UUID)
        user_id: ID of the user
        user_type: Type of user (Team_Member or Ambassador)
        rank: Current rank in leaderboard
        total_pp: Total Panda Points
        updated_at: Timestamp of last cache update
    """
    __tablename__ = "leaderboard_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    user_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    total_pp: Mapped[float] = mapped_column(nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def __init__(self, **kwargs):
        """Initialize LeaderboardCache with user_type validation"""
        # Validate user_type before initialization
        if 'user_type' in kwargs:
            user_type = kwargs['user_type']
            valid_types = ['Team_Member', 'Ambassador']
            if user_type not in valid_types:
                raise ValueError(
                    f"Invalid user_type '{user_type}'. Must be one of: {valid_types}"
                )
        super().__init__(**kwargs)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="leaderboard_cache"
    )

    def __repr__(self) -> str:
        return f"<LeaderboardCache(user_id={self.user_id}, rank={self.rank}, total_pp={self.total_pp})>"


class Schedule(Base):
    """
    Schedule model for calendar events.
    
    Attributes:
        id: Unique identifier (UUID)
        title: Event title
        description: Event description
        event_date: Date/time of the event
        target_group: Target group for the event
        created_by_id: ID of admin who created the event
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        deleted_at: Soft delete timestamp
    """
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    target_group: Mapped[TargetGroup] = mapped_column(
        SQLEnum(TargetGroup, name="target_group", create_type=True),
        nullable=False,
        index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
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
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_schedules",
        foreign_keys=[created_by_id]
    )

    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, title={self.title}, event_date={self.event_date})>"


class Announcement(Base):
    """
    Announcement model for platform announcements.
    
    Attributes:
        id: Unique identifier (UUID)
        title: Announcement title
        content: Announcement content
        target_group: Target group for the announcement
        created_by_id: ID of admin who created the announcement
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        deleted_at: Soft delete timestamp
    """
    __tablename__ = "announcements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_group: Mapped[TargetGroup] = mapped_column(
        SQLEnum(TargetGroup, name="target_group", create_type=False),
        nullable=False,
        index=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
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
        default=None
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_announcements",
        foreign_keys=[created_by_id]
    )

    def __repr__(self) -> str:
        return f"<Announcement(id={self.id}, title={self.title}, target_group={self.target_group})>"

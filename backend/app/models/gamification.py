"""Gamification models for community engagement"""
import uuid
from datetime import datetime, date
from enum import Enum
from sqlalchemy import String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Integer, Boolean, Date, JSON, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BadgeType(str, Enum):
    """Badge type enumeration"""
    TASK_BASED = "Task_Based"
    POINTS_BASED = "Points_Based"
    STREAK_BASED = "Streak_Based"
    SPECIAL = "Special"


class BadgeRarity(str, Enum):
    """Badge rarity enumeration"""
    COMMON = "Common"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"


class LeaderboardPeriod(str, Enum):
    """Leaderboard time period enumeration"""
    ALL_TIME = "All_Time"
    MONTHLY = "Monthly"
    WEEKLY = "Weekly"


class ThemeMode(str, Enum):
    """UI theme mode enumeration"""
    DARK = "Dark"
    LIGHT = "Light"


class FontSize(str, Enum):
    """Font size enumeration"""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


class AbuseType(str, Enum):
    """Abuse detection type enumeration"""
    REFERRAL_SPAM = "Referral_Spam"
    MULTI_ACCOUNT = "Multi_Account"
    BOT_ACTIVITY = "Bot_Activity"
    SUSPICIOUS_PATTERN = "Suspicious_Pattern"


class AbuseSeverity(str, Enum):
    """Abuse severity level enumeration"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class GameReward(Base):
    """
    GameReward model for tournament winnings and event rewards.
    
    Attributes:
        id: Unique identifier
        game_id: External game system ID
        game_name: Name of the game
        tournament_name: Name of the tournament
        winner_user_id: Community user who won
        reward_amount: Panda Points to award
        placement: Winner's placement (1st, 2nd, 3rd, etc.)
        is_claimed: Whether reward has been claimed
        claimed_at: Timestamp of claim
        verification_data: JSON with proof of win
        expires_at: Claim deadline
    """
    __tablename__ = "game_rewards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    game_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tournament_name: Mapped[str] = mapped_column(String(255), nullable=False)
    winner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reward_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        info={"check": "reward_amount > 0"}
    )
    placement: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        info={"check": "placement > 0"}
    )
    is_claimed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    verification_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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

    # Relationships
    winner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[winner_user_id]
    )

    def __repr__(self) -> str:
        return f"<GameReward(id={self.id}, game={self.game_name}, winner={self.winner_user_id})>"


class Badge(Base):
    """
    Badge model for achievement awards.
    
    Attributes:
        id: Unique identifier
        name: Badge name (unique)
        description: Badge description
        icon_url: URL to badge icon image
        badge_type: Type of badge (Task_Based, Points_Based, etc.)
        criteria: JSON with achievement criteria
        rarity: Badge rarity level
        points_reward: Bonus points for earning badge
    """
    __tablename__ = "badges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon_url: Mapped[str] = mapped_column(String(500), nullable=False)
    badge_type: Mapped[BadgeType] = mapped_column(
        SQLEnum(BadgeType, name="badge_type", create_type=True),
        nullable=False,
        index=True
    )
    criteria: Mapped[dict] = mapped_column(JSON, nullable=False)
    rarity: Mapped[BadgeRarity] = mapped_column(
        SQLEnum(BadgeRarity, name="badge_rarity", create_type=True),
        nullable=False,
        index=True
    )
    points_reward: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.0
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

    # Relationships
    user_badges: Mapped[list["UserBadge"]] = relationship(
        "UserBadge",
        back_populates="badge",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Badge(id={self.id}, name={self.name}, rarity={self.rarity})>"


class UserBadge(Base):
    """
    UserBadge model for tracking earned badges.
    
    Attributes:
        id: Unique identifier
        user_id: User who earned the badge
        badge_id: Badge that was earned
        earned_at: Timestamp of earning
        progress: Progress toward next tier (0.0-1.0)
    """
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
        CheckConstraint("progress >= 0.0 AND progress <= 1.0", name="check_progress_range")
    )

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
        index=True
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("badges.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    progress: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=0.0
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")

    def __repr__(self) -> str:
        return f"<UserBadge(user_id={self.user_id}, badge_id={self.badge_id})>"


class Referral(Base):
    """
    Referral model for tracking user referrals.
    
    Attributes:
        id: Unique identifier
        referrer_id: User who referred
        referee_id: User who was referred (unique)
        referral_code: Code used for referral
        referrer_bonus: Points awarded to referrer
        referee_bonus: Points awarded to referee
        is_bonus_awarded: Whether bonuses have been awarded
        bonus_awarded_at: Timestamp of bonus award
        referee_completed_first_task: Whether referee completed first task
    """
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referee_id", name="uq_referee"),
        CheckConstraint("referrer_id != referee_id", name="check_no_self_referral")
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    referrer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    referee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    referral_code: Mapped[str] = mapped_column(String(8), nullable=False)
    referrer_bonus: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=50.0
    )
    referee_bonus: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=25.0
    )
    is_bonus_awarded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    bonus_awarded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    referee_completed_first_task: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    referrer: Mapped["User"] = relationship("User", foreign_keys=[referrer_id])
    referee: Mapped["User"] = relationship("User", foreign_keys=[referee_id])

    def __repr__(self) -> str:
        return f"<Referral(referrer={self.referrer_id}, referee={self.referee_id})>"


class PublicLeaderboard(Base):
    """
    PublicLeaderboard model for cached leaderboard rankings.
    
    Attributes:
        id: Unique identifier
        user_id: User on leaderboard
        username: Denormalized username for performance
        time_period: Leaderboard period (All_Time, Monthly, Weekly)
        rank: User's rank position
        points_earned: Points earned in period
        tasks_completed: Tasks completed in period
        badges_earned: Badges earned in period
        rank_change: Change from previous period
        period_start: Period start date
        period_end: Period end date
        updated_at: Last update timestamp
    """
    __tablename__ = "public_leaderboard"
    __table_args__ = (
        UniqueConstraint("user_id", "time_period", name="uq_user_period"),
    )

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
        index=True
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    time_period: Mapped[LeaderboardPeriod] = mapped_column(
        SQLEnum(LeaderboardPeriod, name="leaderboard_period", create_type=True),
        nullable=False,
        index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    points_earned: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tasks_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    badges_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rank_change: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<PublicLeaderboard(user={self.username}, period={self.time_period}, rank={self.rank})>"


class UserThemePreference(Base):
    """
    UserThemePreference model for UI customization.
    
    Attributes:
        id: Unique identifier
        user_id: User (unique)
        theme_mode: Dark or Light mode
        accent_color: Hex color code
        enable_animations: Whether animations are enabled
        reduce_motion: Whether to reduce motion for accessibility
        font_size: Font size preference
    """
    __tablename__ = "user_theme_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_theme"),
    )

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
        unique=True
    )
    theme_mode: Mapped[ThemeMode] = mapped_column(
        SQLEnum(ThemeMode, name="theme_mode", create_type=True),
        nullable=False,
        default=ThemeMode.DARK
    )
    accent_color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#00FF88"
    )
    enable_animations: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    reduce_motion: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    font_size: Mapped[FontSize] = mapped_column(
        SQLEnum(FontSize, name="font_size", create_type=True),
        nullable=False,
        default=FontSize.MEDIUM
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

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<UserThemePreference(user_id={self.user_id}, mode={self.theme_mode})>"


class CommunityAnalytics(Base):
    """
    CommunityAnalytics model for daily aggregated metrics.
    
    Attributes:
        id: Unique identifier
        date: Date of aggregation (unique)
        total_users: Total community users
        new_users: New users registered
        active_users: Users with activity in last 7 days
        total_tasks_submitted: Total task submissions
        total_tasks_approved: Total approved submissions
        total_points_awarded: Total points awarded
        total_referrals: Total referrals made
        total_badges_awarded: Total badges awarded
        avg_tasks_per_user: Average tasks per active user
    """
    __tablename__ = "community_analytics"
    __table_args__ = (
        UniqueConstraint("date", name="uq_analytics_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    total_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tasks_submitted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tasks_approved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_points_awarded: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    total_referrals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_badges_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_tasks_per_user: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<CommunityAnalytics(date={self.date}, users={self.total_users})>"


class AbuseDetectionLog(Base):
    """
    AbuseDetectionLog model for tracking suspicious activity.
    
    Attributes:
        id: Unique identifier
        user_id: User being flagged
        abuse_type: Type of abuse detected
        severity: Severity level
        detection_method: Method used to detect abuse
        evidence: JSON with detection details
        is_resolved: Whether issue has been resolved
        resolved_at: Resolution timestamp
        resolved_by_id: Admin who resolved
        action_taken: Description of action taken
    """
    __tablename__ = "abuse_detection_logs"

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
        index=True
    )
    abuse_type: Mapped[AbuseType] = mapped_column(
        SQLEnum(AbuseType, name="abuse_type", create_type=True),
        nullable=False,
        index=True
    )
    severity: Mapped[AbuseSeverity] = mapped_column(
        SQLEnum(AbuseSeverity, name="abuse_severity", create_type=True),
        nullable=False,
        index=True
    )
    detection_method: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    resolved_by: Mapped["User | None"] = relationship("User", foreign_keys=[resolved_by_id])

    def __repr__(self) -> str:
        return f"<AbuseDetectionLog(user={self.user_id}, type={self.abuse_type}, severity={self.severity})>"

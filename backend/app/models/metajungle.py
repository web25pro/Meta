"""Meta-Jungle ecosystem models — quests, NFTs, P2P, staking, campaigns,
learn-to-earn and marketplace redemptions (Master Prompt v3.0, Chapters 5–12).

Enum-like fields are stored as plain strings (validated by Pydantic at the API
layer) so the schema migration is a single atomic step with no PG ``CREATE TYPE``
juggling.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, Numeric, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)


class Quest(Base):
    """A verified earn action (Chapter 5.2)."""
    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = _pk()
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="daily", index=True)
    verification_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    min_role: Mapped[str] = mapped_column(String(32), nullable=False, default="Explorer")
    steps: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class QuestCompletion(Base):
    """A user's attempt/completion of a quest (Chapter 9: quest_completions)."""
    __tablename__ = "quest_completions"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="approved", index=True)
    pp_awarded: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    proof: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)


class NFTHolding(Base):
    """An LPanda NFT held by a user (Chapter 9: nft_holdings)."""
    __tablename__ = "nft_holdings"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contract_address: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    token_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="LPanda")
    tier: Mapped[str] = mapped_column(String(16), nullable=False, default="common")
    daily_pp_rate: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    traits: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    utilities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_staked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class P2POrder(Base):
    """A peer-to-peer PP order with escrow (Chapter 9: p2p_orders)."""
    __tablename__ = "p2p_orders"

    id: Mapped[uuid.UUID] = _pk()
    seller_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    side: Mapped[str] = mapped_column(String(8), nullable=False, default="sell")
    pp_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="NGN")
    payment_method: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)
    escrow_tx: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Stake(Base):
    """A PP/NFT stake with a lock duration and multiplier (Chapter 7: StakingVault)."""
    __tablename__ = "stakes"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset: Mapped[str] = mapped_column(String(64), nullable=False, default="PP")
    pp_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    multiplier: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False, default=1.0)
    lock_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    accrued: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Partner(Base):
    """A brand partner (Chapter 9: partners)."""
    __tablename__ = "partners"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    logo_url: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    tier: Mapped[str] = mapped_column(String(16), nullable=False, default="bronze")
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Campaign(Base):
    """A partner campaign with a PP budget (Chapter 9: campaigns)."""
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = _pk()
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    blurb: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pp_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pp_per_task: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pp_claimed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_participants: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class CampaignParticipation(Base):
    """A user joining a campaign."""
    __tablename__ = "campaign_participations"
    __table_args__ = (UniqueConstraint("campaign_id", "user_id", name="uq_campaign_participation"),)

    id: Mapped[uuid.UUID] = _pk()
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Course(Base):
    """A learn-to-earn course with a quiz (Chapter 13)."""
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = _pk()
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    blurb: Mapped[str] = mapped_column(Text, nullable=False, default="")
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="Beginner")
    lessons: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quiz: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class CourseCompletion(Base):
    """A user's quiz result for a course."""
    __tablename__ = "course_completions"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pp_awarded: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Redemption(Base):
    """A utility-marketplace redemption that spends PP (Chapter 12)."""
    __tablename__ = "redemptions"

    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    product_name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="airtime")
    pp_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voucher_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="completed", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

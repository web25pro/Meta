"""Admin panel schemas (Overall_Admin only)."""
import uuid
from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ── Overview ────────────────────────────────────────────────────────────────
class AdminOverview(BaseModel):
    total_users: int
    banned_users: int
    pp_issued: float
    pp_spent: float
    redemptions: int
    active_campaigns: int
    quests: int
    quest_completions: int
    nfts_held: int


# ── Users ───────────────────────────────────────────────────────────────────
class AdminUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    username: Optional[str] = None
    email: str
    role: str
    user_type: str
    points: float
    is_banned: bool = False
    is_active: bool = True
    email_verified: bool = False
    created_at: datetime


class AdminUserList(BaseModel):
    users: List[AdminUser]
    total: int
    page: int
    page_size: int


class AdminUserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminPointsAdjust(BaseModel):
    amount: float = Field(..., description="Positive to credit, negative to debit")
    reason: str = Field(..., min_length=1)


# ── Quests ──────────────────────────────────────────────────────────────────
class AdminQuestCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = ""
    pp_reward: int = Field(..., gt=0)
    category: str = "daily"
    verification_type: str = "manual"
    min_role: str = "Explorer"
    daily_limit: int = Field(1, ge=1)
    action_url: Optional[str] = None
    screenshot_required: bool = False
    link_required: bool = False
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class AdminQuestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    pp_reward: Optional[int] = Field(None, gt=0)
    category: Optional[str] = None
    verification_type: Optional[str] = None
    min_role: Optional[str] = None
    daily_limit: Optional[int] = Field(None, ge=1)
    action_url: Optional[str] = None
    screenshot_required: Optional[bool] = None
    link_required: Optional[bool] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


# ── Partners & campaigns ────────────────────────────────────────────────────
class AdminPartnerCreate(BaseModel):
    name: str = Field(..., min_length=1)
    tier: str = "bronze"
    logo_url: str = ""
    contact_email: str = ""
    is_verified: bool = True


class AdminPartner(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    tier: str
    is_verified: bool


# Campaign schemas moved to app/schemas/campaign.py — see docs/ARCHITECTURE.md.


# ── NFT grant ───────────────────────────────────────────────────────────────
class AdminNFTGrant(BaseModel):
    user_id: uuid.UUID
    name: str = "LPanda"
    tier: str = Field("common", pattern="^(common|rare|epic|legendary)$")
    daily_pp_rate: int = Field(20, ge=0)


# ── Completions review ──────────────────────────────────────────────────────
class AdminCompletion(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    quest_id: uuid.UUID
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    quest_title: Optional[str] = None
    status: str
    pp_awarded: float
    proof: Optional[Any] = None
    reviewed_by_id: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
    created_at: datetime


class AdminCompletionList(BaseModel):
    completions: List[AdminCompletion]
    total: int


class GenericOk(BaseModel):
    success: bool = True
    message: str = "ok"


# ── Clear site data ────────────────────────────────────────────────────────
class AdminClearDataRequest(BaseModel):
    """Select which data categories to clear. All default to False."""
    points_transactions: bool = Field(False, description="Clear all PP transaction history")
    quest_completions: bool = Field(False, description="Clear all quest completion records")
    submissions: bool = Field(False, description="Clear all task submissions")
    campaign_data: bool = Field(False, description="Clear campaign participations, tasks, and completions")
    leaderboard_cache: bool = Field(False, description="Clear leaderboard cache")
    announcements: bool = Field(False, description="Clear all announcements")
    schedules: bool = Field(False, description="Clear all schedules")
    nft_holdings: bool = Field(False, description="Clear all NFT holdings")
    p2p_orders: bool = Field(False, description="Clear all P2P trade orders")
    stakes: bool = Field(False, description="Clear all staking records")
    redemptions: bool = Field(False, description="Clear all marketplace redemptions")
    audit_logs: bool = Field(False, description="Clear audit logs")
    idempotency_keys: bool = Field(False, description="Clear idempotency key cache")
    deadline_penalties: bool = Field(False, description="Clear applied deadline penalties")
    reset_user_points: bool = Field(False, description="Reset all user points, XP, and levels to zero")


class AdminClearDataResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    cleared: dict = {}

"""Campaign API schemas.

Kept separate from ``schemas/metajungle.py`` so the campaign domain moves as one
unit when the Chapter-8 ``campaign-service`` is extracted.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict


class CampaignStatus(str, Enum):
    """Mirrors the ``ck_campaign_status`` CHECK constraint."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class VerificationType(str, Enum):
    """Same vocabulary as quests; oauth/webhook auto-approve."""
    OAUTH = "oauth"
    WEBHOOK = "webhook"
    MANUAL = "manual"
    SCREENSHOT = "screenshot"
    ON_CHAIN = "on_chain"


class CompletionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ── Public ──────────────────────────────────────────────────────────────────
class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    brand: Optional[str] = None
    title: str
    blurb: str
    pp_budget: int
    pp_per_task: int
    pp_claimed: int
    pp_reserved: int
    pp_available: int = 0
    status: CampaignStatus
    featured: bool
    total_participants: int
    max_participants: Optional[int] = None
    target_regions: List[str] = []
    target_roles: List[str] = []
    min_role: str
    joined: bool = False
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int


class CampaignTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    campaign_id: uuid.UUID
    title: str
    description: str
    pp_reward: int
    verification_type: VerificationType
    daily_limit: int
    action_url: Optional[str] = None
    order_index: int
    is_active: bool
    completed_today: int = 0
    can_complete: bool = True


class CampaignTaskListResponse(BaseModel):
    tasks: List[CampaignTaskResponse]
    total: int


class EligibilityResponse(BaseModel):
    eligible: bool
    reason: Optional[str] = None
    role: str
    earn_multiplier: float


class CampaignTaskCompleteRequest(BaseModel):
    proof: Optional[dict] = None


class CampaignTaskCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    campaign_id: uuid.UUID
    task_id: uuid.UUID
    status: CompletionStatus
    pp_awarded: float
    created_at: datetime


# ── Admin ───────────────────────────────────────────────────────────────────
class CampaignCreate(BaseModel):
    partner_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    blurb: str = ""
    pp_budget: int = Field(..., ge=0)
    pp_per_task: int = Field(..., ge=0)
    days: int = Field(30, gt=0)
    featured: bool = False
    status: CampaignStatus = CampaignStatus.DRAFT
    target_regions: List[str] = []
    target_roles: List[str] = []
    min_role: str = "Explorer"
    max_participants: Optional[int] = Field(None, gt=0)


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus


class CampaignTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    pp_reward: int = Field(..., ge=0)
    verification_type: VerificationType = VerificationType.MANUAL
    daily_limit: int = Field(1, gt=0)
    action_url: Optional[str] = None
    order_index: int = 0


class CampaignTaskActiveUpdate(BaseModel):
    is_active: bool


class CampaignReviewRequest(BaseModel):
    approve: bool


class CampaignDeleteResponse(BaseModel):
    success: bool
    message: str
    #: Pending completions auto-rejected so their reserved PP is released.
    rejected_pending: int = 0


class PendingCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    campaign_id: uuid.UUID
    campaign_title: Optional[str] = None
    task_id: uuid.UUID
    task_title: Optional[str] = None
    user_id: uuid.UUID
    username: Optional[str] = None
    status: CompletionStatus
    pp_awarded: float
    proof: Optional[Any] = None
    created_at: datetime


class PendingCompletionListResponse(BaseModel):
    completions: List[PendingCompletionResponse]
    total: int

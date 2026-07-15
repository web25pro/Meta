"""Meta-Jungle API schemas."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict


# ── Reputation (Chapter 6) ──────────────────────────────────────────────────
class ReputationResponse(BaseModel):
    user_id: uuid.UUID
    activity_score: int = Field(..., ge=0, le=1000)
    reputation_score: int = Field(..., ge=0, le=1000)
    influence_score: int = Field(..., ge=0, le=1000)
    role: str
    earn_multiplier: float
    next_role: Optional[str] = None


# ── Quests (Chapter 5) ──────────────────────────────────────────────────────
class QuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str
    pp_reward: int
    category: str
    verification_type: str
    min_role: str
    steps: Optional[Any] = None
    daily_limit: int
    action_url: Optional[str] = None
    is_active: bool
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class QuestListResponse(BaseModel):
    quests: List[QuestResponse]
    total: int


class QuestCompleteRequest(BaseModel):
    proof: Optional[dict] = Field(default=None, description="Verification proof payload")


class QuestCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    quest_id: uuid.UUID
    status: str
    pp_awarded: float
    proof: Optional[Any] = None
    created_at: datetime


# ── NFT Vault (Chapter 4.7) ─────────────────────────────────────────────────
class NFTResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    tier: str
    daily_pp_rate: int
    contract_address: str
    token_id: str
    traits: Optional[Any] = None
    utilities: Optional[Any] = None
    is_staked: bool


class NFTListResponse(BaseModel):
    nfts: List[NFTResponse]
    total: int
    total_daily_yield: int


# ── P2P (Chapter 4.5) ───────────────────────────────────────────────────────
class P2POrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    side: str
    pp_amount: int
    price: float
    currency: str
    payment_method: str
    status: str
    seller_id: Optional[uuid.UUID] = None
    buyer_id: Optional[uuid.UUID] = None
    created_at: datetime


class P2POrderListResponse(BaseModel):
    orders: List[P2POrderResponse]
    total: int


class P2POrderCreate(BaseModel):
    side: str = Field(..., pattern="^(buy|sell)$")
    pp_amount: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    currency: str = Field(default="NGN", max_length=8)
    payment_method: str = Field(..., min_length=1, max_length=64)


# ── Staking (Chapter 7) ─────────────────────────────────────────────────────
class StakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    asset: str
    pp_amount: int
    multiplier: float
    lock_days: int
    accrued: float
    status: str
    started_at: datetime
    unlocked_at: Optional[datetime] = None


class StakeListResponse(BaseModel):
    stakes: List[StakeResponse]
    total_staked: int
    total_accrued: float


class StakeCreate(BaseModel):
    pp_amount: int = Field(..., gt=0)
    lock_days: int = Field(..., description="One of 30, 90, 180")


# ── Campaigns (Chapter 11) ──────────────────────────────────────────────────
class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    brand: Optional[str] = None
    title: str
    blurb: str
    pp_budget: int
    pp_per_task: int
    pp_claimed: int
    status: str
    featured: bool
    total_participants: int
    ends_at: Optional[datetime] = None


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int


# ── Learn (Chapter 13) ──────────────────────────────────────────────────────
class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    blurb: str
    level: str
    lessons: int
    pp_reward: int


class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    total: int


class QuizSubmitRequest(BaseModel):
    answers: List[int] = Field(..., description="Selected option index per question")


class QuizResultResponse(BaseModel):
    passed: bool
    score: int
    pp_awarded: float


# ── Marketplace (Chapter 12) ────────────────────────────────────────────────
class RedeemRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    destination: Optional[str] = Field(default=None, description="Phone, meter, email, etc.")


class RedemptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product_id: str
    product_name: str
    category: str
    pp_cost: int
    destination: Optional[str] = None
    voucher_code: str
    status: str
    created_at: datetime


class MarketProduct(BaseModel):
    id: str
    category: str
    name: str
    pp: int
    fiat: str
    provider: str
    regions: List[str]
    input: str


class MarketCatalogResponse(BaseModel):
    products: List[MarketProduct]

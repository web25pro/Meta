"""LPanda Premium membership schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import uuid


class WalletConnectRequest(BaseModel):
    """Request to connect an EVM wallet address."""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"wallet_address": "0x1234567890abcdef1234567890abcdef12345678"}]
        }
    )

    wallet_address: str = Field(
        ...,
        min_length=42,
        max_length=42,
        description="EVM wallet address (0x-prefixed, 42 chars)",
        examples=["0x1234567890abcdef1234567890abcdef12345678"],
    )


class TierBenefitsResponse(BaseModel):
    """Benefits/permissions for a single tier."""
    daily_quest_limit: Optional[int] = None
    monthly_campaign_limit: Optional[int] = None
    can_create_campaign: bool = False
    campaign_feature_level: str = "none"
    can_use_media: bool = False
    can_create_video_contest: bool = False
    can_create_bounty: bool = False


class NextTierInfo(BaseModel):
    """Progress toward the next membership tier."""
    name: str
    nfts_required: int
    nfts_needed: int


class WalletConnectResponse(BaseModel):
    """Response after connecting a wallet and verifying NFTs."""
    model_config = ConfigDict(from_attributes=True)

    tier: str
    tier_name: str
    nft_count: int
    wallet_address: str
    benefits: TierBenefitsResponse
    next_tier: Optional[NextTierInfo] = None


class QuestUsageInfo(BaseModel):
    """Quest usage for the current day."""
    used: int
    limit: Optional[int] = None
    unlimited: bool = False


class CampaignUsageInfo(BaseModel):
    """Campaign participation usage for the current month."""
    used: int
    limit: Optional[int] = None
    unlimited: bool = False


class UsageInfo(BaseModel):
    """Combined usage information."""
    quests_today: QuestUsageInfo
    campaigns_this_month: CampaignUsageInfo


class MembershipStatusResponse(BaseModel):
    """Full membership status for the dashboard / premium page."""
    model_config = ConfigDict(from_attributes=True)

    tier: str
    tier_name: str
    nft_count: int
    wallet_address: Optional[str] = None
    wallet_verified_at: Optional[str] = None
    tier_updated_at: Optional[str] = None
    usage: UsageInfo
    permissions: TierBenefitsResponse
    next_tier: Optional[NextTierInfo] = None
    available_points: float = 0.0
    locked_points: float = 0.0
    escrow_points: float = 0.0


class TierInfoItem(BaseModel):
    """A single tier's configuration for the comparison page."""
    key: str
    name: str
    nft_required: int
    daily_quest_limit: Optional[int] = None
    monthly_campaign_limit: Optional[int] = None
    can_create_campaign: bool = False
    campaign_feature_level: str = "none"
    can_use_media: bool = False
    can_create_video_contest: bool = False
    can_create_bounty: bool = False
    description: str = ""


class TierListResponse(BaseModel):
    """All membership tiers for the comparison UI."""
    tiers: List[TierInfoItem]

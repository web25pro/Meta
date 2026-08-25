"""LPanda Premium membership API endpoints.

Handles wallet connection, NFT verification, tier assignment, and membership
status queries.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.tier_config import get_all_tiers
from app.models.user import User
from app.api.user import get_current_user
from app.services.wallet_service import WalletService
from app.services.premium_service import PremiumService
from app.schemas.premium import (
    WalletConnectRequest,
    WalletConnectResponse,
    MembershipStatusResponse,
    TierListResponse,
    TierInfoItem,
    TierBenefitsResponse,
    NextTierInfo,
    QuestUsageInfo,
    CampaignUsageInfo,
    UsageInfo,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/premium", tags=["premium"])


@router.post("/connect-wallet", response_model=WalletConnectResponse)
async def connect_wallet(
    body: WalletConnectRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Connect an EVM wallet and verify LPanda NFT ownership.

    Queries the blockchain for the wallet's NFT balance, determines the
    appropriate membership tier, and saves it against the user's account.
    """
    try:
        result = await WalletService.verify_and_update_tier(
            db=db,
            user_id=current_user.id,
            wallet_address=body.wallet_address,
        )
        return WalletConnectResponse(
            tier=result["tier"],
            tier_name=result["tier_name"],
            nft_count=result["nft_count"],
            wallet_address=result["wallet_address"],
            benefits=TierBenefitsResponse(**result["benefits"]),
            next_tier=NextTierInfo(**result["next_tier"]) if result["next_tier"] else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/revalidate", response_model=WalletConnectResponse)
async def revalidate_nft_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Re-check the user's NFT balance and update tier if changed.

    Use this to force a refresh without waiting for the cache to expire.
    """
    try:
        result = await WalletService.revalidate_tier(
            db=db,
            user_id=current_user.id,
        )
        return WalletConnectResponse(
            tier=result["tier"],
            tier_name=result["tier_name"],
            nft_count=result["nft_count"],
            wallet_address=result["wallet_address"],
            benefits=TierBenefitsResponse(**result["benefits"]),
            next_tier=NextTierInfo(**result["next_tier"]) if result["next_tier"] else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status", response_model=MembershipStatusResponse)
async def get_membership_status(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the current user's full membership status.

    Includes tier, NFT count, usage counters, permissions, and next-tier
    progress.
    """
    try:
        result = await PremiumService.get_membership_status(
            db=db,
            user_id=current_user.id,
        )
        return MembershipStatusResponse(
            tier=result["tier"],
            tier_name=result["tier_name"],
            nft_count=result["nft_count"],
            wallet_address=result["wallet_address"],
            wallet_verified_at=result["wallet_verified_at"],
            tier_updated_at=result["tier_updated_at"],
            usage=UsageInfo(
                quests_today=QuestUsageInfo(**result["usage"]["quests_today"]),
                campaigns_this_month=CampaignUsageInfo(**result["usage"]["campaigns_this_month"]),
            ),
            permissions=TierBenefitsResponse(**result["permissions"]),
            next_tier=NextTierInfo(**result["next_tier"]) if result["next_tier"] else None,
            available_points=result["available_points"],
            locked_points=result["locked_points"],
            escrow_points=result["escrow_points"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/tiers", response_model=TierListResponse)
async def list_tiers():
    """Get all membership tier configurations.

    Returns the full tier comparison data for the premium page.
    No authentication required.
    """
    tiers = get_all_tiers()
    return TierListResponse(
        tiers=[TierInfoItem(**t) for t in tiers]
    )

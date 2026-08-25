"""Centralized LPanda membership tier permission checks.

All tier-gated operations should call this service instead of duplicating tier
logic throughout the application.  The service reads the user's current
``membership_tier`` column and cross-references ``tier_config``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.tier_config import (
    MEMBERSHIP_TIERS,
    get_tier_config,
    get_tier_permissions,
    get_next_tier,
    get_all_tiers,
)
from app.models.user import User
from app.models.metajungle import CampaignParticipation, QuestCompletion

logger = get_logger(__name__)


class PremiumService:
    """Centralized membership permission checks."""

    # ── Tier lookup ──────────────────────────────────────────────────────────

    @staticmethod
    async def get_user_tier(db: AsyncSession, user_id: uuid.UUID) -> str:
        """Return the user's current membership tier key."""
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier = result.scalar_one_or_none()
        return tier or "standard"

    # ── Quest limits ─────────────────────────────────────────────────────────

    @staticmethod
    async def can_join_quest(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, str]:
        """Check whether the user can complete another quest today.

        Returns ``(allowed, reason)``.  ``reason`` is empty when allowed.
        """
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier_key = result.scalar_one_or_none() or "standard"
        cfg = get_tier_config(tier_key)
        limit = cfg["daily_quest_limit"]  # None == unlimited

        if limit is None:
            return True, ""

        # Count today's quest completions (all statuses count toward the limit)
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        count_result = await db.execute(
            select(func.count())
            .select_from(QuestCompletion)
            .where(
                QuestCompletion.user_id == user_id,
                QuestCompletion.created_at >= start_of_day,
            )
        )
        used = int(count_result.scalar() or 0)

        if used >= limit:
            tier_name = cfg["name"]
            return False, (
                f"Daily quest limit reached ({used}/{limit}). "
                f"Upgrade your LPanda membership to unlock more quest opportunities."
            )
        return True, ""

    # ── Campaign participation limits ────────────────────────────────────────

    @staticmethod
    async def can_join_campaign(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, str]:
        """Check whether the user can join another campaign this month.

        Returns ``(allowed, reason)``.
        """
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier_key = result.scalar_one_or_none() or "standard"
        cfg = get_tier_config(tier_key)
        limit = cfg["monthly_campaign_limit"]  # None == unlimited

        if limit is None:
            return True, ""

        # Count participations this calendar month
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count_result = await db.execute(
            select(func.count())
            .select_from(CampaignParticipation)
            .where(
                CampaignParticipation.user_id == user_id,
                CampaignParticipation.created_at >= start_of_month,
            )
        )
        used = int(count_result.scalar() or 0)

        if used >= limit:
            tier_name = cfg["name"]
            return False, (
                f"Monthly campaign limit reached ({used}/{limit}). "
                f"Upgrade your LPanda membership to participate in more campaigns."
            )
        return True, ""

    # ── Campaign creation permissions ────────────────────────────────────────

    @staticmethod
    async def can_create_campaign(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, str]:
        """Check whether the user is allowed to create campaigns."""
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier_key = result.scalar_one_or_none() or "standard"
        cfg = get_tier_config(tier_key)

        if not cfg["can_create_campaign"]:
            return False, (
                "Campaign creation requires Panda Pro or Panda Elite membership. "
                "Hold at least 3 LPanda NFTs to unlock."
            )
        return True, ""

    @staticmethod
    async def can_use_media_campaign(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, str]:
        """Check whether the user can use media (image/video) in campaigns."""
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier_key = result.scalar_one_or_none() or "standard"
        cfg = get_tier_config(tier_key)

        if not cfg["can_use_media"]:
            return False, (
                "Image and video campaigns require Panda Elite membership. "
                "Hold at least 5 LPanda NFTs to unlock."
            )
        return True, ""

    @staticmethod
    async def can_create_video_contest(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, str]:
        """Check whether the user can create video contests."""
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier_key = result.scalar_one_or_none() or "standard"
        cfg = get_tier_config(tier_key)

        if not cfg["can_create_video_contest"]:
            return False, (
                "Video contests require Panda Elite membership. "
                "Hold at least 5 LPanda NFTs to unlock."
            )
        return True, ""

    @staticmethod
    async def can_create_bounty(
        db: AsyncSession, user_id: uuid.UUID
    ) -> tuple[bool, str]:
        """Check whether the user can create bounties."""
        result = await db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier_key = result.scalar_one_or_none() or "standard"
        cfg = get_tier_config(tier_key)

        if not cfg["can_create_bounty"]:
            return False, (
                "Bounties require Panda Elite membership. "
                "Hold at least 5 LPanda NFTs to unlock."
            )
        return True, ""

    # ── Full membership status ───────────────────────────────────────────────

    @staticmethod
    async def get_membership_status(
        db: AsyncSession, user_id: uuid.UUID
    ) -> dict:
        """Return the user's full membership status for the dashboard / premium page.

        Includes tier info, NFT count, usage counters, and next-tier progress.
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        tier_key = user.membership_tier or "standard"
        cfg = get_tier_config(tier_key)
        now = datetime.now(timezone.utc)

        # Quest usage today
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        quest_count_result = await db.execute(
            select(func.count())
            .select_from(QuestCompletion)
            .where(
                QuestCompletion.user_id == user_id,
                QuestCompletion.created_at >= start_of_day,
            )
        )
        quests_used_today = int(quest_count_result.scalar() or 0)

        # Campaign participation this month
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        campaign_count_result = await db.execute(
            select(func.count())
            .select_from(CampaignParticipation)
            .where(
                CampaignParticipation.user_id == user_id,
                CampaignParticipation.created_at >= start_of_month,
            )
        )
        campaigns_used_this_month = int(campaign_count_result.scalar() or 0)

        # NFT count from the holdings table (admin-granted NFTs)
        from app.models.metajungle import NFTHolding
        nft_result = await db.execute(
            select(func.count())
            .select_from(NFTHolding)
            .where(NFTHolding.user_id == user_id)
        )
        nft_count = int(nft_result.scalar() or 0)

        # Next tier info
        next_tier = get_next_tier(tier_key)
        next_info = None
        if next_tier:
            next_name, next_nfts = next_tier
            next_info = {
                "name": next_name,
                "nfts_required": next_nfts,
                "nfts_needed": max(0, next_nfts - nft_count),
            }

        return {
            "tier": tier_key,
            "tier_name": cfg["name"],
            "nft_count": nft_count,
            "wallet_address": user.wallet_address,
            "wallet_verified_at": user.wallet_verified_at.isoformat() if user.wallet_verified_at else None,
            "tier_updated_at": user.tier_updated_at.isoformat() if user.tier_updated_at else None,
            "usage": {
                "quests_today": {
                    "used": quests_used_today,
                    "limit": cfg["daily_quest_limit"],
                    "unlimited": cfg["daily_quest_limit"] is None,
                },
                "campaigns_this_month": {
                    "used": campaigns_used_this_month,
                    "limit": cfg["monthly_campaign_limit"],
                    "unlimited": cfg["monthly_campaign_limit"] is None,
                },
            },
            "permissions": get_tier_permissions(tier_key),
            "next_tier": next_info,
            "available_points": float(user.available_points or 0),
            "locked_points": float(user.locked_points or 0),
            "escrow_points": float(user.escrow_points or 0),
        }

    @staticmethod
    async def should_revalidate(user: User) -> bool:
        """Return True if the user's NFT balance should be re-checked.

        Uses the ``NFT_VERIFICATION_CACHE_MINUTES`` setting to determine
        staleness.
        """
        if not user.wallet_verified_at:
            return True
        cache_minutes = settings.NFT_VERIFICATION_CACHE_MINUTES
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cache_minutes)
        return user.wallet_verified_at < cutoff

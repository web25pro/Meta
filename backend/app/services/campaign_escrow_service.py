"""Campaign escrow management for user-created performance-based campaigns.

Handles funding, reward distribution, and refunds for campaigns with the
escrow model: creator locks PP → participants earn → ranked qualifiers receive
rewards → unused PP returned.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.user import User
from app.models.metajungle import Campaign, CampaignParticipation, CampaignRanking
from app.models.points_and_audit import TransactionType
from app.services.points_service import PointsService

logger = get_logger(__name__)


class CampaignEscrowService:
    """Campaign escrow funding, distribution, and refund logic."""

    # ── Funding ──────────────────────────────────────────────────────────────

    @staticmethod
    async def fund_campaign(
        db: AsyncSession,
        user_id: uuid.UUID,
        campaign_id: uuid.UUID,
    ) -> dict:
        """Lock PP from the campaign creator into escrow.

        The campaign must be in ``funding_required`` status.  The creator must
        have sufficient available PP.  On success the campaign moves to
        ``funded``.
        """
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id).with_for_update()
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        if campaign.creator_id != user_id:
            raise ValueError("Only the campaign creator can fund it")
        if campaign.status != "funding_required":
            raise ValueError(f"Campaign is not awaiting funding (status: {campaign.status})")

        required = campaign.total_escrow
        if required <= 0:
            raise ValueError("Campaign escrow amount is not set")

        # Check creator balance
        user = (await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )).scalar_one()
        available = float(user.available_points or 0)
        if available < required:
            raise ValueError(
                f"Insufficient PP balance. Required: {required}, Available: {available:.2f}"
            )

        # Deduct PP from creator
        await PointsService.create_transaction(
            db=db,
            user_id=user_id,
            amount=-required,
            transaction_type=TransactionType.CAMPAIGN_FUNDING,
            reason=f"Campaign escrow funding: {campaign.title}",
            bucket="available",
            source_type="campaign_funding",
            source_id=str(campaign_id),
            idempotency_key=f"campaign_fund:{campaign_id}",
        )

        # Update campaign status
        campaign.status = "funded"
        campaign.pp_budget = required
        await db.flush()
        await db.refresh(campaign)

        return {
            "campaign_id": str(campaign_id),
            "escrow_amount": required,
            "status": "funded",
        }

    # ── Reward distribution ──────────────────────────────────────────────────

    @staticmethod
    async def distribute_rewards(
        db: AsyncSession,
        campaign_id: uuid.UUID,
    ) -> dict:
        """Distribute rewards to qualified participants after ranking.

        Reads the ``campaign_rankings`` table for qualified participants,
        credits PP from escrow, and returns unused PP to the creator.
        """
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id).with_for_update()
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        if campaign.status not in ("completed", "active", "ended"):
            raise ValueError(f"Campaign cannot distribute rewards (status: {campaign.status})")

        # Get qualified rankings ordered by rank
        rankings = (await db.execute(
            select(CampaignRanking)
            .where(
                CampaignRanking.campaign_id == campaign_id,
                CampaignRanking.qualified == True,
            )
            .order_by(CampaignRanking.rank)
        )).scalars().all()

        pp_per_qualifier = campaign.pp_per_qualifier
        distributed = 0
        reward_count = 0

        for ranking in rankings:
            # Credit PP to the participant
            await PointsService.create_transaction(
                db=db,
                user_id=ranking.user_id,
                amount=pp_per_qualifier,
                transaction_type=TransactionType.CAMPAIGN_REWARD,
                reason=f"Campaign reward: {campaign.title} (rank #{ranking.rank})",
                bucket="available",
                source_type="campaign_reward",
                source_id=str(campaign_id),
                idempotency_key=f"campaign_reward:{campaign_id}:{ranking.user_id}",
            )
            distributed += pp_per_qualifier
            reward_count += 1

            # Update participation record
            participation = (await db.execute(
                select(CampaignParticipation).where(
                    CampaignParticipation.campaign_id == campaign_id,
                    CampaignParticipation.user_id == ranking.user_id,
                )
            )).scalar_one_or_none()
            if participation:
                participation.pp_earned = pp_per_qualifier

        # Refund unused PP to creator
        unused = campaign.total_escrow - distributed
        refunded = 0
        if unused > 0 and campaign.creator_id:
            await PointsService.create_transaction(
                db=db,
                user_id=campaign.creator_id,
                amount=unused,
                transaction_type=TransactionType.CAMPAIGN_REFUND,
                reason=f"Campaign escrow refund: {campaign.title} ({reward_count}/{campaign.num_qualifiers} qualifiers)",
                bucket="available",
                source_type="campaign_refund",
                source_id=str(campaign_id),
                idempotency_key=f"campaign_refund:{campaign_id}",
            )
            refunded = unused

        # Update campaign
        campaign.pp_distributed = distributed
        campaign.pp_refunded = refunded
        campaign.status = "rewards_distributed"
        await db.flush()

        return {
            "campaign_id": str(campaign_id),
            "distributed": distributed,
            "refunded": refunded,
            "qualifiers_paid": reward_count,
            "qualifiers_configured": campaign.num_qualifiers,
        }

    # ── Refund (cancel) ──────────────────────────────────────────────────────

    @staticmethod
    async def refund_campaign(
        db: AsyncSession,
        campaign_id: uuid.UUID,
    ) -> dict:
        """Return all escrowed PP to the creator (campaign cancelled)."""
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id).with_for_update()
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        if campaign.status not in ("funded", "funding_required"):
            raise ValueError(f"Campaign cannot be refunded (status: {campaign.status})")
        if not campaign.creator_id:
            raise ValueError("Cannot refund an admin campaign")

        refund_amount = campaign.total_escrow
        if refund_amount <= 0:
            refund_amount = campaign.pp_budget

        if refund_amount > 0:
            await PointsService.create_transaction(
                db=db,
                user_id=campaign.creator_id,
                amount=refund_amount,
                transaction_type=TransactionType.CAMPAIGN_REFUND,
                reason=f"Campaign cancelled — escrow refunded: {campaign.title}",
                bucket="available",
                source_type="campaign_refund",
                source_id=str(campaign_id),
                idempotency_key=f"campaign_cancel_refund:{campaign_id}",
            )

        campaign.pp_refunded = refund_amount
        campaign.status = "ended"
        await db.flush()

        return {
            "campaign_id": str(campaign_id),
            "refunded": refund_amount,
            "status": "ended",
        }

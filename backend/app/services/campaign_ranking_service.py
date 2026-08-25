"""Campaign ranking and leaderboard service.

Calculates engagement scores for campaign participants and generates ranked
leaderboards.  Used by the escrow service to determine reward qualifiers.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.user import User
from app.models.metajungle import (
    Campaign,
    CampaignParticipation,
    CampaignTask,
    CampaignTaskCompletion,
    CampaignRanking,
    QuestCompletion,
)
from app.models.points_and_audit import PointsTransaction, TransactionType

logger = get_logger(__name__)


class CampaignRankingService:
    """Campaign participant scoring and ranking."""

    # ── Score calculation ────────────────────────────────────────────────────

    @staticmethod
    async def calculate_scores(
        db: AsyncSession,
        campaign_id: uuid.UUID,
    ) -> list[dict]:
        """Compute engagement scores for all participants in a campaign.

        Scoring factors (configurable via ``campaign.ranking_criteria``):
        - Tasks completed within the campaign
        - Approved completions (quality filter)
        - Total PP earned in the campaign
        - Quest completions during the campaign period (cross-platform activity)
        - Referral count (if configured)

        Returns a list of ``{user_id, score, metrics}`` dicts, unsorted.
        """
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")

        # Get all participants
        participations = (await db.execute(
            select(CampaignParticipation).where(
                CampaignParticipation.campaign_id == campaign_id
            )
        )).scalars().all()

        if not participations:
            return []

        # Get campaign tasks
        tasks = (await db.execute(
            select(CampaignTask).where(
                CampaignTask.campaign_id == campaign_id,
                CampaignTask.is_active == True,
            )
        )).scalars().all()
        task_ids = [t.id for t in tasks]

        # Ranking criteria weights (defaults)
        criteria = campaign.ranking_criteria or {}
        w_tasks = criteria.get("task_weight", 1.0)
        w_approved = criteria.get("approved_weight", 1.5)
        w_pp = criteria.get("pp_weight", 0.01)

        scores = []
        for part in participations:
            # Count task completions
            if task_ids:
                total_completions = int((await db.execute(
                    select(func.count())
                    .select_from(CampaignTaskCompletion)
                    .where(
                        CampaignTaskCompletion.campaign_id == campaign_id,
                        CampaignTaskCompletion.user_id == part.user_id,
                        CampaignTaskCompletion.task_id.in_(task_ids),
                    )
                )).scalar() or 0)

                approved_completions = int((await db.execute(
                    select(func.count())
                    .select_from(CampaignTaskCompletion)
                    .where(
                        CampaignTaskCompletion.campaign_id == campaign_id,
                        CampaignTaskCompletion.user_id == part.user_id,
                        CampaignTaskCompletion.task_id.in_(task_ids),
                        CampaignTaskCompletion.status == "approved",
                    )
                )).scalar() or 0)
            else:
                total_completions = 0
                approved_completions = 0

            # PP earned in this campaign
            pp_earned = float(part.pp_earned or 0)

            # Calculate composite score
            score = (
                total_completions * w_tasks
                + approved_completions * w_approved
                + pp_earned * w_pp
            )

            metrics = {
                "tasks_completed": total_completions,
                "tasks_approved": approved_completions,
                "pp_earned": pp_earned,
            }

            scores.append({
                "user_id": part.user_id,
                "score": round(score, 2),
                "metrics": metrics,
            })

        return scores

    # ── Leaderboard generation ───────────────────────────────────────────────

    @staticmethod
    async def generate_leaderboard(
        db: AsyncSession,
        campaign_id: uuid.UUID,
    ) -> list[dict]:
        """Rank participants and determine qualifiers.

        Returns a sorted list of participants with rank, score, and
        qualification status.
        """
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")

        scores = await CampaignRankingService.calculate_scores(db, campaign_id)
        if not scores:
            return []

        # Sort by score descending
        scores.sort(key=lambda x: x["score"], reverse=True)

        num_qualifiers = campaign.num_qualifiers
        leaderboard = []
        for i, entry in enumerate(scores):
            rank = i + 1
            qualified = rank <= num_qualifiers and entry["score"] > 0
            leaderboard.append({
                "user_id": str(entry["user_id"]),
                "rank": rank,
                "score": entry["score"],
                "metrics": entry["metrics"],
                "qualified": qualified,
            })

        return leaderboard

    # ── Finalize campaign ────────────────────────────────────────────────────

    @staticmethod
    async def finalize_campaign(
        db: AsyncSession,
        campaign_id: uuid.UUID,
    ) -> dict:
        """End a campaign: calculate rankings, save to DB, and return results.

        Does NOT distribute rewards — call ``CampaignEscrowService.distribute_rewards``
        separately after this.
        """
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")

        leaderboard = await CampaignRankingService.generate_leaderboard(db, campaign_id)

        # Save rankings to DB
        # First, clear any existing rankings for this campaign
        existing = await db.execute(
            select(CampaignRanking).where(CampaignRanking.campaign_id == campaign_id)
        )
        for row in existing.scalars().all():
            await db.delete(row)

        for entry in leaderboard:
            ranking = CampaignRanking(
                campaign_id=campaign_id,
                user_id=uuid.UUID(entry["user_id"]),
                score=entry["score"],
                metrics=entry["metrics"],
                rank=entry["rank"],
                qualified=entry["qualified"],
            )
            db.add(ranking)

        campaign.status = "completed"
        await db.flush()

        qualifiers = [e for e in leaderboard if e["qualified"]]
        return {
            "campaign_id": str(campaign_id),
            "total_participants": len(leaderboard),
            "qualifiers": len(qualifiers),
            "leaderboard": leaderboard[:20],  # Top 20 for response
            "status": "completed",
        }

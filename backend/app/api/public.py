"""Public API endpoints (no authentication required)

These endpoints serve data for the landing page and other public-facing
parts of the application. They are rate-limited but do not require JWT.
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models import User, UserType, Campaign, Partner

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/public", tags=["public"])


@router.get("/stats")
async def get_public_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Aggregated platform stats for the landing page ticker.

    Returns:
        - total_users: total registered (non-deleted) users
        - total_pp_earned: sum of all points across users
        - active_campaigns: count of campaigns with status=active
    """
    try:
        # Total users
        user_count = await db.execute(
            select(func.count()).select_from(User).where(User.deleted_at.is_(None))
        )
        total_users = user_count.scalar() or 0

        # Total PP earned
        pp_sum = await db.execute(
            select(func.coalesce(func.sum(User.points), 0)).where(User.deleted_at.is_(None))
        )
        total_pp = float(pp_sum.scalar() or 0)

        # Active campaigns
        campaign_count = await db.execute(
            select(func.count()).select_from(Campaign).where(Campaign.status == "active")
        )
        active_campaigns = campaign_count.scalar() or 0

        return {
            "total_users": total_users,
            "total_pp_earned": total_pp,
            "active_campaigns": active_campaigns,
        }
    except Exception as e:
        logger.error(f"Error fetching public stats: {e}")
        return {
            "total_users": 0,
            "total_pp_earned": 0,
            "active_campaigns": 0,
        }


@router.get("/leaderboard")
async def get_public_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(5, ge=1, le=20, description="Number of entries"),
):
    """
    Top ambassadors by PP for the landing page leaderboard preview.

    Returns a list of {rank, username, pp} objects.
    """
    try:
        result = await db.execute(
            select(User)
            .where(User.deleted_at.is_(None), User.user_type == UserType.AMBASSADOR)
            .order_by(User.points.desc())
            .limit(limit)
        )
        users = result.scalars().all()

        return [
            {
                "rank": i + 1,
                "username": u.username or u.name,
                "pp": float(u.points),
            }
            for i, u in enumerate(users)
        ]
    except Exception as e:
        logger.error(f"Error fetching public leaderboard: {e}")
        return []


@router.get("/partners")
async def get_public_partners(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    List of verified partner names for the landing page partner strip.
    """
    try:
        result = await db.execute(
            select(Partner).where(Partner.is_verified == True)  # noqa: E712
        )
        partners = result.scalars().all()
        return [p.name for p in partners]
    except Exception as e:
        logger.error(f"Error fetching public partners: {e}")
        return []

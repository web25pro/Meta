"""Campaign API endpoints — public and admin.

Extracted from ``api/metajungle.py`` as part of the campaign module boundary
(see ``docs/ARCHITECTURE.md:47`` — campaign-service).
"""
import uuid
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.api.user import get_current_user, get_economic_user
from app.api.admin import require_admin
from app.services.campaign_service import CampaignService
from app.services.premium_service import PremiumService
from app.services.campaign_escrow_service import CampaignEscrowService
from app.services.campaign_ranking_service import CampaignRankingService
from app.schemas.campaign import (
    CampaignListResponse,
    CampaignResponse,
    CampaignTaskListResponse,
    CampaignTaskResponse,
    EligibilityResponse,
    CampaignTaskCompleteRequest,
    CampaignTaskCompletionResponse,
    CampaignWithdrawalResponse,
    CampaignCreate,
    CampaignStatusUpdate,
    CampaignFeaturedUpdate,
    CampaignTaskCreate,
    CampaignTaskUpdate,
    CampaignTaskActiveUpdate,
    CampaignReviewRequest,
    CampaignDeleteResponse,
    PendingCompletionListResponse,
    PendingCompletionResponse,
)
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

CurrentUser = Annotated[User, Depends(get_current_user)]
EconomicUser = Annotated[User, Depends(get_economic_user)]
Admin = Annotated[User, Depends(require_admin)]
DB = Annotated[AsyncSession, Depends(get_db)]


def _bad(e: Exception, code: int = status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=code, detail=str(e))


# ── Public router ───────────────────────────────────────────────────────────
campaigns_router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


@campaigns_router.get("", response_model=CampaignListResponse)
async def list_campaigns(current_user: CurrentUser, db: DB):
    """Active campaigns inside their date window, eligibility-annotated."""
    campaigns = await CampaignService.list_campaigns(db, current_user)
    return {"campaigns": campaigns, "total": len(campaigns)}


@campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: uuid.UUID, current_user: CurrentUser, db: DB):
    try:
        return await CampaignService.get_public_campaign(db, current_user, campaign_id)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@campaigns_router.get("/{campaign_id}/eligibility", response_model=EligibilityResponse)
async def check_eligibility(campaign_id: uuid.UUID, current_user: CurrentUser, db: DB):
    try:
        campaign = await CampaignService.get_public_campaign(db, current_user, campaign_id)
        return await CampaignService.check_eligibility(db, current_user, campaign)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@campaigns_router.post("/{campaign_id}/join")
async def join_campaign(campaign_id: uuid.UUID, current_user: EconomicUser, db: DB):
    try:
        await CampaignService.join_campaign(db, current_user, campaign_id)
        return {"success": True, "message": "Joined campaign"}
    except ValueError as e:
        raise _bad(e)


@campaigns_router.post(
    "/{campaign_id}/withdraw",
    response_model=CampaignWithdrawalResponse,
)
async def withdraw_campaign_points(campaign_id: uuid.UUID, current_user: EconomicUser, db: DB):
    try:
        return await CampaignService.withdraw_points(db, current_user, campaign_id)
    except ValueError as e:
        raise _bad(e)


@campaigns_router.get("/{campaign_id}/tasks", response_model=CampaignTaskListResponse)
async def list_tasks(campaign_id: uuid.UUID, current_user: CurrentUser, db: DB):
    try:
        tasks = await CampaignService.list_tasks(db, campaign_id, current_user)
        return {"tasks": tasks, "total": len(tasks)}
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@campaigns_router.post(
    "/{campaign_id}/tasks/{task_id}/complete",
    response_model=CampaignTaskCompletionResponse,
)
async def complete_task(
    campaign_id: uuid.UUID,
    task_id: uuid.UUID,
    body: CampaignTaskCompleteRequest,
    current_user: EconomicUser,
    db: DB,
):
    try:
        return await CampaignService.complete_task(
            db, current_user, campaign_id, task_id, body.proof,
        )
    except ValueError as e:
        raise _bad(e)


# ── User campaign creation ──────────────────────────────────────────────────

class UserCampaignCreateRequest(BaseModel):
    """Request to create a user campaign (Panda Pro / Panda Elite only)."""
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "title": "Summer Engagement Campaign",
                "description": "Complete social tasks to earn rewards",
                "campaign_type": "engagement",
                "num_qualifiers": 10,
                "pp_per_qualifier": 50,
                "starts_at": "2026-09-01T00:00:00Z",
                "ends_at": "2026-09-30T23:59:59Z",
                "required_actions": ["follow", "like", "retweet"],
                "ranking_criteria": {"task_weight": 1.0, "approved_weight": 1.5},
            }]
        }
    )

    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field("", max_length=5000)
    campaign_type: str = Field("text", description="text, image, video, engagement, video_contest, bounty")
    num_qualifiers: int = Field(..., gt=0, le=1000)
    pp_per_qualifier: int = Field(..., gt=0)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    required_actions: Optional[List[str]] = None
    ranking_criteria: Optional[dict] = None
    max_participants: Optional[int] = None
    target_regions: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)


class UserCampaignResponse(BaseModel):
    """Response for user-created campaign operations."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    campaign_type: str
    status: str
    num_qualifiers: int
    pp_per_qualifier: int
    total_escrow: int
    pp_distributed: int
    pp_refunded: int
    total_participants: int
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None


class CampaignFundResponse(BaseModel):
    """Response after funding a campaign."""
    campaign_id: str
    escrow_amount: int
    status: str


class CampaignLeaderboardEntry(BaseModel):
    """A single entry in the campaign leaderboard."""
    user_id: str
    rank: int
    score: float
    metrics: dict
    qualified: bool


class CampaignLeaderboardResponse(BaseModel):
    """Campaign leaderboard response."""
    campaign_id: str
    total_participants: int
    qualifiers: int
    leaderboard: List[CampaignLeaderboardEntry]


class MyCampaignsResponse(BaseModel):
    """List of user's created campaigns."""
    campaigns: List[UserCampaignResponse]
    total: int


# Allowed campaign types per tier
_USER_CAMPAIGN_TYPES = {"text", "engagement"}
_ELITE_CAMPAIGN_TYPES = {"text", "engagement", "image", "video", "video_contest", "bounty"}


def _slugify(title: str) -> str:
    """Generate a URL-safe slug from a title."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:60]


@campaigns_router.post("/create", response_model=UserCampaignResponse)
async def create_user_campaign(
    body: UserCampaignCreateRequest,
    current_user: EconomicUser,
    db: DB,
):
    """Create a campaign (Panda Pro or Panda Elite only).

    Panda Pro can create text/engagement campaigns.
    Panda Elite can create all campaign types including image, video, video_contest, bounty.
    """
    # Check permission
    can_create, reason = await PremiumService.can_create_campaign(db, current_user.id)
    if not can_create:
        raise _bad(ValueError(reason))

    # Validate campaign type against tier
    tier = await PremiumService.get_user_tier(db, current_user.id)
    if tier == "panda_pro" and body.campaign_type not in _USER_CAMPAIGN_TYPES:
        raise _bad(ValueError(
            f"Panda Pro can only create text and engagement campaigns. "
            f"Upgrade to Panda Elite for {body.campaign_type} campaigns."
        ))
    if body.campaign_type not in _ELITE_CAMPAIGN_TYPES:
        raise _bad(ValueError(f"Unknown campaign type: {body.campaign_type}"))

    # Media check for image/video types
    if body.campaign_type in ("image", "video", "video_contest", "bounty"):
        can_media, media_reason = await PremiumService.can_use_media_campaign(db, current_user.id)
        if not can_media:
            raise _bad(ValueError(media_reason))

    # Video contest check
    if body.campaign_type == "video_contest":
        can_vc, vc_reason = await PremiumService.can_create_video_contest(db, current_user.id)
        if not can_vc:
            raise _bad(ValueError(vc_reason))

    # Bounty check
    if body.campaign_type == "bounty":
        can_b, b_reason = await PremiumService.can_create_bounty(db, current_user.id)
        if not can_b:
            raise _bad(ValueError(b_reason))

    # Calculate escrow
    total_escrow = body.num_qualifiers * body.pp_per_qualifier

    # Check creator has enough PP
    available = float(current_user.available_points or 0)
    if available < total_escrow:
        raise _bad(ValueError(
            f"Insufficient PP. Required: {total_escrow}, Available: {available:.2f}"
        ))

    # Generate unique slug
    base_slug = _slugify(body.title)
    slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"

    # Parse dates
    from datetime import datetime as dt
    starts = dt.fromisoformat(body.starts_at) if body.starts_at else None
    ends = dt.fromisoformat(body.ends_at) if body.ends_at else None

    # Create campaign
    from app.models.metajungle import Campaign
    campaign = Campaign(
        creator_id=current_user.id,
        slug=slug,
        title=body.title,
        blurb=body.description[:200],
        description=body.description,
        campaign_type=body.campaign_type,
        num_qualifiers=body.num_qualifiers,
        pp_per_qualifier=body.pp_per_qualifier,
        total_escrow=total_escrow,
        status="funding_required",
        max_participants=body.max_participants,
        target_regions=body.target_regions,
        target_roles=body.target_roles,
        required_actions=body.required_actions,
        ranking_criteria=body.ranking_criteria,
        starts_at=starts,
        ends_at=ends,
    )
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)

    return UserCampaignResponse(
        id=str(campaign.id),
        title=campaign.title,
        description=campaign.description,
        campaign_type=campaign.campaign_type,
        status=campaign.status,
        num_qualifiers=campaign.num_qualifiers,
        pp_per_qualifier=campaign.pp_per_qualifier,
        total_escrow=campaign.total_escrow,
        pp_distributed=campaign.pp_distributed,
        pp_refunded=campaign.pp_refunded,
        total_participants=campaign.total_participants,
        starts_at=campaign.starts_at.isoformat() if campaign.starts_at else None,
        ends_at=campaign.ends_at.isoformat() if campaign.ends_at else None,
    )


@campaigns_router.post("/{campaign_id}/fund", response_model=CampaignFundResponse)
async def fund_campaign(
    campaign_id: uuid.UUID,
    current_user: EconomicUser,
    db: DB,
):
    """Fund a campaign from the creator's PP balance.

    Moves the required escrow amount from available PP into campaign escrow.
    """
    try:
        result = await CampaignEscrowService.fund_campaign(db, current_user.id, campaign_id)
        return CampaignFundResponse(**result)
    except ValueError as e:
        raise _bad(e)


@campaigns_router.get("/my-campaigns", response_model=MyCampaignsResponse)
async def list_my_campaigns(
    current_user: CurrentUser,
    db: DB,
):
    """List campaigns created by the current user."""
    from app.models.metajungle import Campaign
    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.creator_id == current_user.id,
            Campaign.deleted_at.is_(None),
        )
        .order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()
    items = [
        UserCampaignResponse(
            id=str(c.id),
            title=c.title,
            description=c.description,
            campaign_type=c.campaign_type,
            status=c.status,
            num_qualifiers=c.num_qualifiers,
            pp_per_qualifier=c.pp_per_qualifier,
            total_escrow=c.total_escrow,
            pp_distributed=c.pp_distributed,
            pp_refunded=c.pp_refunded,
            total_participants=c.total_participants,
            starts_at=c.starts_at.isoformat() if c.starts_at else None,
            ends_at=c.ends_at.isoformat() if c.ends_at else None,
        )
        for c in campaigns
    ]
    return MyCampaignsResponse(campaigns=items, total=len(items))


@campaigns_router.get("/{campaign_id}/leaderboard", response_model=CampaignLeaderboardResponse)
async def get_campaign_leaderboard(
    campaign_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
):
    """Get the ranked leaderboard for a campaign."""
    try:
        leaderboard = await CampaignRankingService.generate_leaderboard(db, campaign_id)
        from app.models.metajungle import Campaign
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        return CampaignLeaderboardResponse(
            campaign_id=str(campaign_id),
            total_participants=len(leaderboard),
            qualifiers=len([e for e in leaderboard if e["qualified"]]),
            leaderboard=[CampaignLeaderboardEntry(**e) for e in leaderboard],
        )
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@campaigns_router.post("/{campaign_id}/finalize")
async def finalize_campaign(
    campaign_id: uuid.UUID,
    current_user: EconomicUser,
    db: DB,
):
    """Finalize a campaign: rank participants and distribute rewards.

    Only the campaign creator can finalize. Calculates rankings, distributes
    PP to qualifiers, and refunds unused escrow.
    """
    from app.models.metajungle import Campaign
    campaign = (await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )).scalar_one_or_none()
    if not campaign:
        raise _bad(ValueError("Campaign not found"), status.HTTP_404_NOT_FOUND)
    if campaign.creator_id != current_user.id:
        raise _bad(ValueError("Only the campaign creator can finalize"), status.HTTP_403_FORBIDDEN)

    try:
        # Rank participants
        rank_result = await CampaignRankingService.finalize_campaign(db, campaign_id)
        # Distribute rewards
        dist_result = await CampaignEscrowService.distribute_rewards(db, campaign_id)
        return {
            "ranking": rank_result,
            "distribution": dist_result,
        }
    except ValueError as e:
        raise _bad(e)


# ── Admin router ────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/api/v1/admin/campaigns", tags=["admin-campaigns"])


@admin_router.get("", response_model=list[CampaignResponse])
async def admin_list_campaigns(admin: Admin, db: DB):
    return await CampaignService.admin_list_campaigns(db)


@admin_router.post("", response_model=CampaignResponse)
async def admin_create_campaign(body: CampaignCreate, admin: Admin, db: DB):
    try:
        return await CampaignService.create_campaign(db, body)
    except ValueError as e:
        raise _bad(e)


@admin_router.patch("/{campaign_id}", response_model=CampaignResponse)
@admin_router.patch("/{campaign_id}/status", response_model=CampaignResponse)
async def admin_set_campaign_status(
    campaign_id: uuid.UUID, body: CampaignStatusUpdate, admin: Admin, db: DB
):
    """Move a campaign through its lifecycle.

    The bare ``/{campaign_id}`` form is the original admin path, kept so existing
    clients and tests keep working.
    """
    try:
        return await CampaignService.set_campaign_status(db, campaign_id, body.status.value)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.patch("/{campaign_id}/featured", response_model=CampaignResponse)
async def admin_set_campaign_featured(
    campaign_id: uuid.UUID,
    body: CampaignFeaturedUpdate,
    admin: Admin,
    db: DB,
):
    try:
        return await CampaignService.set_campaign_featured(db, campaign_id, body.featured)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.get("/{campaign_id}/tasks", response_model=CampaignTaskListResponse)
async def admin_list_tasks(campaign_id: uuid.UUID, admin: Admin, db: DB):
    try:
        tasks = await CampaignService.list_tasks(db, campaign_id)
        return {"tasks": tasks, "total": len(tasks)}
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.post("/{campaign_id}/tasks", response_model=CampaignTaskResponse)
async def admin_create_task(campaign_id: uuid.UUID, body: CampaignTaskCreate, admin: Admin, db: DB):
    try:
        return await CampaignService.create_task(db, campaign_id, body)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.patch(
    "/{campaign_id}/tasks/{task_id}",
    response_model=CampaignTaskResponse,
)
async def admin_update_task(
    campaign_id: uuid.UUID,
    task_id: uuid.UUID,
    body: CampaignTaskUpdate,
    admin: Admin,
    db: DB,
):
    try:
        return await CampaignService.update_task(db, campaign_id, task_id, body)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.patch(
    "/{campaign_id}/tasks/{task_id}/active",
    response_model=CampaignTaskResponse,
)
async def admin_set_task_active(
    campaign_id: uuid.UUID,
    task_id: uuid.UUID,
    body: CampaignTaskActiveUpdate,
    admin: Admin,
    db: DB,
):
    try:
        return await CampaignService.set_task_active(
            db, campaign_id, task_id, body.is_active,
        )
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.delete("/{campaign_id}", response_model=CampaignDeleteResponse)
async def admin_delete_campaign(campaign_id: uuid.UUID, admin: Admin, db: DB):
    """Soft delete a campaign, releasing reserved budget.

    Pending completions are rejected so their PP leaves the review queue.
    Approved completions keep their ledger entries — the audit trail survives.
    """
    try:
        result = await CampaignService.delete_campaign(db, admin, campaign_id)
        return {
            "success": True,
            "message": "Campaign deleted",
            "rejected_pending": result["rejected_pending"],
        }
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@admin_router.get("/review-queue", response_model=PendingCompletionListResponse)
async def admin_list_pending_completions(admin: Admin, db: DB):
    completions = await CampaignService.list_pending_completions(db)
    return {"completions": completions, "total": len(completions)}


@admin_router.post(
    "/review-queue/{completion_id}",
    response_model=CampaignTaskCompletionResponse,
)
async def admin_review_completion(
    completion_id: uuid.UUID, body: CampaignReviewRequest, admin: Admin, db: DB
):
    try:
        return await CampaignService.review_completion(db, admin, completion_id, body.approve, body.reason)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)

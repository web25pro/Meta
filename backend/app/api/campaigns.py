"""Campaign API endpoints — public and admin.

Extracted from ``api/metajungle.py`` as part of the campaign module boundary
(see ``docs/ARCHITECTURE.md:47`` — campaign-service).
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.api.user import get_current_user, get_economic_user
from app.api.admin import require_admin
from app.services.campaign_service import CampaignService
from app.schemas.campaign import (
    CampaignListResponse,
    CampaignResponse,
    CampaignTaskListResponse,
    CampaignTaskResponse,
    EligibilityResponse,
    CampaignTaskCompleteRequest,
    CampaignTaskCompletionResponse,
    CampaignCreate,
    CampaignStatusUpdate,
    CampaignTaskCreate,
    CampaignTaskActiveUpdate,
    CampaignReviewRequest,
    CampaignDeleteResponse,
    PendingCompletionListResponse,
    PendingCompletionResponse,
)

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
        return await CampaignService.get_campaign(db, campaign_id)
    except ValueError as e:
        raise _bad(e, status.HTTP_404_NOT_FOUND)


@campaigns_router.get("/{campaign_id}/eligibility", response_model=EligibilityResponse)
async def check_eligibility(campaign_id: uuid.UUID, current_user: CurrentUser, db: DB):
    try:
        campaign = await CampaignService.get_campaign(db, campaign_id)
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

"""Admin panel API (Overall_Admin only)."""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User, UserRole
from app.api.user import get_current_user
from app.services.admin_service import AdminService
from app.schemas.admin import (
    AdminOverview, AdminUserList, AdminUser, AdminUserUpdate, AdminPointsAdjust,
    AdminQuestCreate, AdminQuestUpdate,
    AdminPartnerCreate, AdminPartner, AdminCampaignCreate, AdminCampaignStatus,
    AdminNFTGrant, AdminCompletionList, GenericOk,
)
from app.schemas.metajungle import QuestResponse, CampaignResponse, NFTResponse


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Allow only Overall_Admin."""
    role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role != UserRole.OVERALL_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


Admin = Annotated[User, Depends(require_admin)]
DB = Annotated[AsyncSession, Depends(get_db)]

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _bad(e: Exception):
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── Overview ────────────────────────────────────────────────────────────────
@router.get("/overview", response_model=AdminOverview)
async def overview(admin: Admin, db: DB):
    return await AdminService.overview(db)


# ── Users ───────────────────────────────────────────────────────────────────
@router.get("/users", response_model=AdminUserList)
async def list_users(admin: Admin, db: DB, page: int = Query(1, ge=1),
                     page_size: int = Query(20, ge=1, le=100), q: Optional[str] = None):
    users, total = await AdminService.list_users(db, page, page_size, q)
    return {"users": users, "total": total, "page": page, "page_size": page_size}


@router.patch("/users/{user_id}", response_model=AdminUser)
async def update_user(user_id: uuid.UUID, body: AdminUserUpdate, admin: Admin, db: DB):
    try:
        u = await AdminService.update_user(db, user_id, body.role, body.is_active)
        return AdminUser(
            id=u.id, name=u.name, username=u.username, email=u.email,
            role=u.role.value if hasattr(u.role, "value") else u.role,
            user_type=u.user_type.value if hasattr(u.user_type, "value") else u.user_type,
            points=float(u.points or 0), is_banned=not u.is_active, is_active=u.is_active,
            email_verified=u.email_verified, created_at=u.created_at,
        )
    except ValueError as e:
        raise _bad(e)


@router.post("/users/{user_id}/points", response_model=GenericOk)
async def adjust_points(user_id: uuid.UUID, body: AdminPointsAdjust, admin: Admin, db: DB):
    try:
        await AdminService.adjust_points(db, user_id, body.amount, body.reason)
        return {"success": True, "message": "Points adjusted"}
    except ValueError as e:
        raise _bad(e)


# ── Quests ──────────────────────────────────────────────────────────────────
@router.get("/quests", response_model=list[QuestResponse])
async def list_quests(admin: Admin, db: DB):
    return await AdminService.list_quests(db)


@router.post("/quests", response_model=QuestResponse)
async def create_quest(body: AdminQuestCreate, admin: Admin, db: DB):
    return await AdminService.create_quest(db, body)


@router.patch("/quests/{quest_id}", response_model=QuestResponse)
async def update_quest(quest_id: uuid.UUID, body: AdminQuestUpdate, admin: Admin, db: DB):
    try:
        return await AdminService.update_quest(db, quest_id, body)
    except ValueError as e:
        raise _bad(e)


@router.delete("/quests/{quest_id}", response_model=GenericOk)
async def delete_quest(quest_id: uuid.UUID, admin: Admin, db: DB):
    try:
        await AdminService.delete_quest(db, quest_id)
        return {"success": True, "message": "Quest deleted"}
    except ValueError as e:
        raise _bad(e)


# ── Partners & campaigns ────────────────────────────────────────────────────
@router.get("/partners", response_model=list[AdminPartner])
async def list_partners(admin: Admin, db: DB):
    return await AdminService.list_partners(db)


@router.post("/partners", response_model=AdminPartner)
async def create_partner(body: AdminPartnerCreate, admin: Admin, db: DB):
    return await AdminService.create_partner(db, body)


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(admin: Admin, db: DB):
    return await AdminService.list_campaigns(db)


@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(body: AdminCampaignCreate, admin: Admin, db: DB):
    try:
        return await AdminService.create_campaign(db, body)
    except ValueError as e:
        raise _bad(e)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def set_campaign_status(campaign_id: uuid.UUID, body: AdminCampaignStatus, admin: Admin, db: DB):
    try:
        return await AdminService.set_campaign_status(db, campaign_id, body.status)
    except ValueError as e:
        raise _bad(e)


# ── NFT grant ───────────────────────────────────────────────────────────────
@router.post("/nft/grant", response_model=NFTResponse)
async def grant_nft(body: AdminNFTGrant, admin: Admin, db: DB):
    try:
        return await AdminService.grant_nft(db, body)
    except ValueError as e:
        raise _bad(e)


# ── Completions review ──────────────────────────────────────────────────────
@router.get("/quest-completions", response_model=AdminCompletionList)
async def list_completions(admin: Admin, db: DB, status: Optional[str] = Query(None)):
    rows = await AdminService.list_completions(db, status)
    return {"completions": rows, "total": len(rows)}


@router.post("/quest-completions/{completion_id}/review", response_model=GenericOk)
async def review_completion(completion_id: uuid.UUID, admin: Admin, db: DB, approve: bool = Query(True)):
    try:
        await AdminService.review_completion(db, completion_id, approve)
        return {"success": True, "message": "Reviewed"}
    except ValueError as e:
        raise _bad(e)

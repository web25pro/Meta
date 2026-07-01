"""Meta-Jungle ecosystem API endpoints (Chapters 5–13)."""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models import User
from app.api.user import get_current_user
from app.services.metajungle_service import MetaJungleService, MARKET_CATALOG
from app.schemas.metajungle import (
    ReputationResponse,
    QuestListResponse, QuestResponse, QuestCompleteRequest, QuestCompletionResponse,
    NFTListResponse, NFTResponse,
    P2POrderListResponse, P2POrderResponse, P2POrderCreate,
    StakeListResponse, StakeResponse, StakeCreate,
    CampaignListResponse, CampaignResponse,
    CourseListResponse, CourseResponse, QuizSubmitRequest, QuizResultResponse,
    RedeemRequest, RedemptionResponse, MarketCatalogResponse,
)

logger = get_logger(__name__)

CurrentUser = Annotated[User, Depends(get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]


def _bad(e: Exception, code: int = status.HTTP_400_BAD_REQUEST):
    return HTTPException(status_code=code, detail=str(e))


# ── Reputation ──────────────────────────────────────────────────────────────
reputation_router = APIRouter(prefix="/api/v1/reputation", tags=["reputation"])


@reputation_router.get("/me", response_model=ReputationResponse)
async def get_my_reputation(current_user: CurrentUser, db: DB):
    """Get the caller's three reputation scores, role and earn multiplier."""
    return await MetaJungleService.compute_reputation(db, current_user)


# ── Quests ──────────────────────────────────────────────────────────────────
quests_router = APIRouter(prefix="/api/v1/quests", tags=["quests"])


@quests_router.get("", response_model=QuestListResponse)
async def list_quests(current_user: CurrentUser, db: DB):
    quests = await MetaJungleService.list_quests(db)
    return {"quests": quests, "total": len(quests)}


@quests_router.post("/{quest_id}/complete", response_model=QuestCompletionResponse)
async def complete_quest(quest_id: uuid.UUID, body: QuestCompleteRequest, current_user: CurrentUser, db: DB):
    try:
        return await MetaJungleService.complete_quest(db, current_user, quest_id, body.proof)
    except ValueError as e:
        raise _bad(e)


# ── NFT Vault ───────────────────────────────────────────────────────────────
nft_router = APIRouter(prefix="/api/v1/nft", tags=["nft"])


@nft_router.get("", response_model=NFTListResponse)
async def list_nfts(current_user: CurrentUser, db: DB):
    nfts, daily = await MetaJungleService.list_nfts(db, current_user.id)
    return {"nfts": nfts, "total": len(nfts), "total_daily_yield": daily}


# ── P2P ─────────────────────────────────────────────────────────────────────
p2p_router = APIRouter(prefix="/api/v1/p2p", tags=["p2p"])


@p2p_router.get("/orders", response_model=P2POrderListResponse)
async def list_orders(current_user: CurrentUser, db: DB, side: Optional[str] = Query(None, pattern="^(buy|sell)$")):
    orders = await MetaJungleService.list_orders(db, side)
    return {"orders": orders, "total": len(orders)}


@p2p_router.post("/orders", response_model=P2POrderResponse)
async def create_order(body: P2POrderCreate, current_user: CurrentUser, db: DB):
    try:
        return await MetaJungleService.create_order(db, current_user, body)
    except ValueError as e:
        raise _bad(e)


# ── Staking ─────────────────────────────────────────────────────────────────
staking_router = APIRouter(prefix="/api/v1/staking", tags=["staking"])


@staking_router.get("", response_model=StakeListResponse)
async def list_stakes(current_user: CurrentUser, db: DB):
    stakes, total_staked, accrued = await MetaJungleService.list_stakes(db, current_user.id)
    return {"stakes": stakes, "total_staked": total_staked, "total_accrued": accrued}


@staking_router.post("", response_model=StakeResponse)
async def create_stake(body: StakeCreate, current_user: CurrentUser, db: DB):
    try:
        return await MetaJungleService.create_stake(db, current_user, body.pp_amount, body.lock_days)
    except ValueError as e:
        raise _bad(e)


@staking_router.post("/{stake_id}/claim", response_model=StakeResponse)
async def claim_stake(stake_id: uuid.UUID, current_user: CurrentUser, db: DB):
    try:
        return await MetaJungleService.claim_stake(db, current_user, stake_id)
    except ValueError as e:
        raise _bad(e)


# ── Campaigns ───────────────────────────────────────────────────────────────
campaigns_router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


@campaigns_router.get("", response_model=CampaignListResponse)
async def list_campaigns(current_user: CurrentUser, db: DB):
    campaigns = await MetaJungleService.list_campaigns(db)
    return {"campaigns": campaigns, "total": len(campaigns)}


@campaigns_router.post("/{campaign_id}/join")
async def join_campaign(campaign_id: uuid.UUID, current_user: CurrentUser, db: DB):
    try:
        await MetaJungleService.join_campaign(db, current_user, campaign_id)
        return {"success": True, "message": "Joined campaign"}
    except ValueError as e:
        raise _bad(e)


# ── Learn ───────────────────────────────────────────────────────────────────
learn_router = APIRouter(prefix="/api/v1/learn", tags=["learn"])


@learn_router.get("/courses", response_model=CourseListResponse)
async def list_courses(current_user: CurrentUser, db: DB):
    courses = await MetaJungleService.list_courses(db)
    return {"courses": courses, "total": len(courses)}


@learn_router.post("/courses/{course_id}/quiz", response_model=QuizResultResponse)
async def submit_quiz(course_id: uuid.UUID, body: QuizSubmitRequest, current_user: CurrentUser, db: DB):
    try:
        return await MetaJungleService.submit_quiz(db, current_user, course_id, body.answers)
    except ValueError as e:
        raise _bad(e)


# ── Marketplace ─────────────────────────────────────────────────────────────
marketplace_router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])


@marketplace_router.get("/catalog", response_model=MarketCatalogResponse)
async def get_catalog(current_user: CurrentUser):
    return {"products": MARKET_CATALOG}


@marketplace_router.post("/redeem", response_model=RedemptionResponse)
async def redeem(body: RedeemRequest, current_user: CurrentUser, db: DB):
    try:
        return await MetaJungleService.redeem(db, current_user, body.product_id, body.destination)
    except ValueError as e:
        raise _bad(e)


routers = [
    reputation_router, quests_router, nft_router, p2p_router,
    staking_router, campaigns_router, learn_router, marketplace_router,
]

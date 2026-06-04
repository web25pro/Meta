"""Points and rewards API endpoints"""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models import User, UserRole
from app.services.points_service import PointsService
from app.services.leaderboard_service import LeaderboardService
from app.schemas.points import (
    PointsTransactionResponse, 
    PointsTransactionListResponse,
    UserPointsResponse,
    AdminBonusRequest,
    AdminPenaltyRequest
)
from app.api.user import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/points", tags=["points"])


@router.get("/balance", response_model=UserPointsResponse)
async def get_my_points_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get current user's Panda Points (PP) balance and rank.
    """
    rank = await LeaderboardService.get_user_rank(db, current_user.id, current_user.user_type)
    
    return {
        "user_id": current_user.id,
        "points": current_user.points,
        "rank": rank
    }


@router.get("/transactions", response_model=PointsTransactionListResponse)
async def get_my_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get current user's points transaction history.
    """
    transactions, total = await PointsService.get_user_transactions(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/balance/{user_id}", response_model=UserPointsResponse)
async def get_user_points_balance(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get any user's points balance (Admin only).
    """
    if current_user.role not in [UserRole.OVERALL_ADMIN, UserRole.AMBASSADOR_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    try:
        points = await PointsService.get_user_points(db, user_id)
        # We'd need user_type to get rank, but for now just returning points
        return {
            "user_id": user_id,
            "points": points,
            "rank": None
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/bonus", response_model=PointsTransactionResponse)
async def award_bonus_points(
    bonus_data: AdminBonusRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Award custom bonus points to a user (Admin only).
    """
    try:
        transaction = await PointsService.assign_admin_bonus(
            db=db,
            user_id=bonus_data.user_id,
            amount=bonus_data.amount,
            reason=bonus_data.reason,
            admin_role=current_user.role,
            admin_user_id=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return transaction
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/penalty", response_model=PointsTransactionResponse)
async def apply_penalty_points(
    penalty_data: AdminPenaltyRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request
):
    """
    Apply custom penalty points to a user (Admin only).
    """
    try:
        transaction = await PointsService.apply_admin_penalty(
            db=db,
            user_id=penalty_data.user_id,
            amount=penalty_data.amount,
            reason=penalty_data.reason,
            admin_role=current_user.role,
            admin_user_id=current_user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        return transaction
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

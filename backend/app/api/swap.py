"""PP ↔ Token swap API endpoints."""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.api.user import get_current_user
from app.services.swap_service import SwapService
from app.schemas.swap import (
    SwapQuoteRequest,
    SwapQuoteResponse,
    SwapExecuteRequest,
    SwapExecuteResponse,
    SwapHistoryItem,
    SwapHistoryResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/swap", tags=["swap"])


@router.get("/quote", response_model=SwapQuoteResponse)
async def get_swap_quote(
    pp_amount: float = Query(..., gt=0, description="PP amount to swap"),
    direction: str = Query("pp_to_token", description="Swap direction"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Get a preview quote for a swap without executing it."""
    try:
        quote = await SwapService.get_quote(
            db=db,
            user_id=current_user.id,
            pp_amount=pp_amount,
            direction=direction,
        )
        return SwapQuoteResponse(**quote)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/execute", response_model=SwapExecuteResponse)
async def execute_swap(
    body: SwapExecuteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Execute a PP ↔ token swap.

    Deducts PP from the user's available balance and records the transaction.
    """
    try:
        result = await SwapService.execute_swap(
            db=db,
            user_id=current_user.id,
            pp_amount=body.pp_amount,
            direction=body.direction,
            quote_id=body.quote_id,
        )
        return SwapExecuteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/history", response_model=SwapHistoryResponse)
async def get_swap_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get the user's swap transaction history."""
    items, total = await SwapService.get_swap_history(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return SwapHistoryResponse(
        items=[SwapHistoryItem(**i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if page_size else 0,
    )

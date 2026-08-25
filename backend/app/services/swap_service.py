"""Panda Points ↔ Token swap service.

Provides a modular swap interface with configurable exchange rates, fees, and
daily limits.  The underlying swap mechanism can be replaced without changing
the API surface.
"""

from __future__ import annotations

import uuid
import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.config import settings
from app.models.user import User
from app.models.points_and_audit import PointsTransaction, PPLedgerEntry, TransactionType
from app.services.points_service import PointsService

logger = get_logger(__name__)

# ── Swap configuration ───────────────────────────────────────────────────────
# These could be moved to Settings or a dedicated config table later.

SWAP_RATE_PP_PER_TOKEN = 100       # 100 PP = 1 token (base rate)
SWAP_FEE_PERCENT = 2.0             # 2% fee on each swap
DAILY_SWAP_LIMIT_PP = 50_000      # Max PP a user can swap per day
MIN_SWAP_PP = 10                   # Minimum swap amount


class SwapService:
    """PP ↔ Token swap logic."""

    # ── Quote ────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_quote(
        db: AsyncSession,
        user_id: uuid.UUID,
        pp_amount: float,
        direction: str = "pp_to_token",
    ) -> dict:
        """Return a preview quote for a swap without executing it.

        ``direction`` is either ``"pp_to_token"`` or ``"token_to_pp"``.
        """
        if direction not in ("pp_to_token", "token_to_pp"):
            raise ValueError("Direction must be 'pp_to_token' or 'token_to_pp'")
        if pp_amount < MIN_SWAP_PP:
            raise ValueError(f"Minimum swap amount is {MIN_SWAP_PP} PP")

        fee = math.floor(pp_amount * SWAP_FEE_PERCENT / 100)
        net_pp = pp_amount - fee

        if direction == "pp_to_token":
            token_amount = net_pp / SWAP_RATE_PP_PER_TOKEN
        else:
            token_amount = net_pp / SWAP_RATE_PP_PER_TOKEN

        return {
            "pp_amount": pp_amount,
            "fee_pp": fee,
            "fee_percent": SWAP_FEE_PERCENT,
            "net_pp": net_pp,
            "token_amount": round(token_amount, 6),
            "rate": SWAP_RATE_PP_PER_TOKEN,
            "direction": direction,
        }

    # ── Validation ───────────────────────────────────────────────────────────

    @staticmethod
    async def validate_swap(
        db: AsyncSession,
        user_id: uuid.UUID,
        pp_amount: float,
        direction: str,
    ) -> tuple[bool, str]:
        """Check whether the user can execute this swap."""
        if pp_amount < MIN_SWAP_PP:
            return False, f"Minimum swap amount is {MIN_SWAP_PP} PP"

        # Check daily limit
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(func.coalesce(func.sum(PointsTransaction.amount), 0))
            .where(
                PointsTransaction.user_id == user_id,
                PointsTransaction.transaction_type == TransactionType.PP_SWAP,
                PointsTransaction.created_at >= start_of_day,
                PointsTransaction.amount < 0,  # debits only
            )
        )
        swapped_today = abs(float(result.scalar() or 0))
        if swapped_today + pp_amount > DAILY_SWAP_LIMIT_PP:
            remaining = max(0, DAILY_SWAP_LIMIT_PP - swapped_today)
            return False, f"Daily swap limit reached. You can swap up to {remaining:.0f} PP today."

        # Check balance
        user_result = await db.execute(
            select(User.available_points).where(User.id == user_id)
        )
        available = float(user_result.scalar() or 0)
        if available < pp_amount:
            return False, f"Insufficient PP balance. Available: {available:.2f} PP"

        return True, ""

    # ── Execution ────────────────────────────────────────────────────────────

    @staticmethod
    async def execute_swap(
        db: AsyncSession,
        user_id: uuid.UUID,
        pp_amount: float,
        direction: str,
        quote_id: Optional[str] = None,
    ) -> dict:
        """Execute a PP ↔ token swap.

        Deducts PP from the user's available balance and records the transaction.
        The actual token transfer is handled by the external swap mechanism
        (not implemented here — this covers the PP side).
        """
        # Validate
        allowed, reason = await SwapService.validate_swap(db, user_id, pp_amount, direction)
        if not allowed:
            raise ValueError(reason)

        # Get quote for fee calculation
        quote = await SwapService.get_quote(db, user_id, pp_amount, direction)
        fee = quote["fee_pp"]
        net_pp = quote["net_pp"]
        token_amount = quote["token_amount"]

        # Deduct PP (the full amount including fee)
        idem_key = f"swap:{user_id}:{quote_id or uuid.uuid4()}"
        tx = await PointsService.create_transaction(
            db=db,
            user_id=user_id,
            amount=-pp_amount,
            transaction_type=TransactionType.PP_SWAP,
            reason=f"Swapped {pp_amount:.0f} PP → {token_amount:.6f} tokens (fee: {fee:.0f} PP)",
            bucket="available",
            source_type="swap",
            idempotency_key=idem_key,
        )

        # Record fee separately if non-zero
        if fee > 0:
            await PointsService.create_transaction(
                db=db,
                user_id=user_id,
                amount=-fee,
                transaction_type=TransactionType.SWAP_FEE,
                reason=f"Swap fee ({SWAP_FEE_PERCENT}%) on {pp_amount:.0f} PP swap",
                bucket="available",
                source_type="swap_fee",
                idempotency_key=f"{idem_key}:fee",
            )

        return {
            "swap_id": str(tx.id),
            "pp_amount": pp_amount,
            "fee_pp": fee,
            "token_amount": token_amount,
            "direction": direction,
            "rate": SWAP_RATE_PP_PER_TOKEN,
            "status": "completed",
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
        }

    # ── History ──────────────────────────────────────────────────────────────

    @staticmethod
    async def get_swap_history(
        db: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Return paginated swap transaction history."""
        offset = (page - 1) * page_size

        # Count
        count_result = await db.execute(
            select(func.count())
            .select_from(PointsTransaction)
            .where(
                PointsTransaction.user_id == user_id,
                PointsTransaction.transaction_type.in_([
                    TransactionType.PP_SWAP,
                    TransactionType.SWAP_FEE,
                ]),
            )
        )
        total = int(count_result.scalar() or 0)

        # Fetch
        result = await db.execute(
            select(PointsTransaction)
            .where(
                PointsTransaction.user_id == user_id,
                PointsTransaction.transaction_type.in_([
                    TransactionType.PP_SWAP,
                    TransactionType.SWAP_FEE,
                ]),
            )
            .order_by(PointsTransaction.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = result.scalars().all()

        items = [
            {
                "id": str(tx.id),
                "amount": float(tx.amount),
                "transaction_type": tx.transaction_type.value if hasattr(tx.transaction_type, 'value') else tx.transaction_type,
                "reason": tx.reason,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in rows
        ]
        return items, total

"""PP ↔ Token swap schemas."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import uuid


class SwapQuoteRequest(BaseModel):
    """Request a swap quote."""
    pp_amount: float = Field(..., gt=0, description="Amount of PP to swap")
    direction: str = Field(
        "pp_to_token",
        description="Swap direction: 'pp_to_token' or 'token_to_pp'",
        pattern="^(pp_to_token|token_to_pp)$",
    )


class SwapQuoteResponse(BaseModel):
    """Preview of a swap without executing."""
    pp_amount: float
    fee_pp: float
    fee_percent: float
    net_pp: float
    token_amount: float
    rate: float
    direction: str


class SwapExecuteRequest(BaseModel):
    """Execute a swap."""
    pp_amount: float = Field(..., gt=0, description="Amount of PP to swap")
    direction: str = Field(
        "pp_to_token",
        description="Swap direction",
        pattern="^(pp_to_token|token_to_pp)$",
    )
    quote_id: Optional[str] = Field(None, description="Optional quote ID for idempotency")


class SwapExecuteResponse(BaseModel):
    """Result of an executed swap."""
    model_config = ConfigDict(from_attributes=True)

    swap_id: str
    pp_amount: float
    fee_pp: float
    token_amount: float
    direction: str
    rate: float
    status: str
    created_at: Optional[str] = None


class SwapHistoryItem(BaseModel):
    """A single swap transaction in history."""
    id: str
    amount: float
    transaction_type: str
    reason: str
    created_at: Optional[str] = None


class SwapHistoryResponse(BaseModel):
    """Paginated swap history."""
    items: List[SwapHistoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int

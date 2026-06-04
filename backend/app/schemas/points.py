"""Points and rewards schemas"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
import uuid

from app.models import TransactionType


class PointsTransactionResponse(BaseModel):
    """
    Points transaction response schema.
    
    Represents a single Panda Points (PP) transaction in the user's history.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "234e5678-e90b-12d3-a456-426614174000",
                    "amount": 50.0,
                    "transaction_type": "Task_Approval",
                    "reason": "Task submission approved",
                    "related_task_id": "345e6789-e01b-23d4-a567-426614174000",
                    "related_submission_id": "456e7890-e12b-34d5-a678-426614174000",
                    "created_at": "2024-01-15T10:30:00Z"
                }
            ]
        }
    )
    
    id: uuid.UUID = Field(
        ...,
        description="Unique transaction identifier",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user who received/lost points",
        examples=["234e5678-e90b-12d3-a456-426614174000"]
    )
    amount: float = Field(
        ...,
        description="Points amount (positive for rewards, negative for penalties)",
        examples=[50.0]
    )
    transaction_type: TransactionType = Field(
        ...,
        description="Type of transaction (Task_Approval, Deadline_Penalty, Admin_Bonus, Admin_Penalty)",
        examples=["Task_Approval"]
    )
    reason: str = Field(
        ...,
        description="Human-readable reason for the transaction",
        examples=["Task submission approved"]
    )
    related_task_id: Optional[uuid.UUID] = Field(
        None,
        description="ID of related task (if applicable)",
        examples=["345e6789-e01b-23d4-a567-426614174000"]
    )
    related_submission_id: Optional[uuid.UUID] = Field(
        None,
        description="ID of related submission (if applicable)",
        examples=["456e7890-e12b-34d5-a678-426614174000"]
    )
    created_at: datetime = Field(
        ...,
        description="Transaction timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )


class PointsTransactionListResponse(BaseModel):
    """
    Paginated points transaction list response.
    
    Contains user's transaction history with pagination metadata.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "transactions": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "user_id": "234e5678-e90b-12d3-a456-426614174000",
                            "amount": 50.0,
                            "transaction_type": "Task_Approval",
                            "reason": "Task submission approved",
                            "related_task_id": "345e6789-e01b-23d4-a567-426614174000",
                            "related_submission_id": "456e7890-e12b-34d5-a678-426614174000",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "total": 42,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    )
    
    transactions: List[PointsTransactionResponse] = Field(
        ...,
        description="List of transactions for current page"
    )
    total: int = Field(
        ...,
        description="Total number of transactions",
        ge=0,
        examples=[42]
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        ge=1,
        examples=[1]
    )
    page_size: int = Field(
        ...,
        description="Number of transactions per page",
        ge=1,
        le=100,
        examples=[20]
    )


class UserPointsResponse(BaseModel):
    """
    User points balance response.
    
    Shows current PP balance and optional leaderboard rank.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "234e5678-e90b-12d3-a456-426614174000",
                    "points": 350.0,
                    "rank": 5
                }
            ]
        }
    )
    
    user_id: uuid.UUID = Field(
        ...,
        description="User identifier",
        examples=["234e5678-e90b-12d3-a456-426614174000"]
    )
    points: float = Field(
        ...,
        description="Current Panda Points (PP) balance",
        examples=[350.0]
    )
    rank: Optional[int] = Field(
        None,
        description="User's current leaderboard rank (if available)",
        examples=[5]
    )


class AdminBonusRequest(BaseModel):
    """
    Admin bonus points request.
    
    Allows admins to award custom bonus points to users.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "234e5678-e90b-12d3-a456-426614174000",
                    "amount": 100.0,
                    "reason": "Exceptional performance on project delivery"
                }
            ]
        }
    )
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user to receive bonus points",
        examples=["234e5678-e90b-12d3-a456-426614174000"]
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Bonus amount (must be positive)",
        examples=[100.0]
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Reason for awarding bonus points",
        examples=["Exceptional performance on project delivery"]
    )


class AdminPenaltyRequest(BaseModel):
    """
    Admin penalty points request.
    
    Allows admins to apply custom penalty points to users.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "234e5678-e90b-12d3-a456-426614174000",
                    "amount": 50.0,
                    "reason": "Policy violation - late submission without notice"
                }
            ]
        }
    )
    
    user_id: uuid.UUID = Field(
        ...,
        description="ID of the user to receive penalty",
        examples=["234e5678-e90b-12d3-a456-426614174000"]
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Penalty amount (must be positive, will be deducted from balance)",
        examples=[50.0]
    )
    reason: str = Field(
        ...,
        min_length=1,
        description="Reason for applying penalty",
        examples=["Policy violation - late submission without notice"]
    )

"""Leaderboard API endpoints"""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token, TokenData
from app.core.logging import get_logger
from app.models import UserType, User
from app.schemas.leaderboard import (
    LeaderboardResponse,
    LeaderboardEntryResponse,
    UserRankResponse
)
from app.services.leaderboard_service import LeaderboardService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid, user not found, or password changed after token issued
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Get user from database
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(
            User.id == uuid.UUID(token_data.user_id),
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Validate token issuance time against password change
    if user.password_changed_at and token_data.iat < user.password_changed_at:
        raise HTTPException(status_code=401, detail="Session invalidated due to password change")
    
    return user


@router.get(
    "/team-members",
    response_model=LeaderboardResponse,
    summary="Get Team Member leaderboard",
    description="""
    Retrieve the leaderboard for Team Members with pagination.
    
    **Authentication Required**: Yes (Bearer token)
    
    **Permissions**: All authenticated users can view the Team Member leaderboard
    
    **Validates**: Requirements 6.1, 6.2, 6.5
    
    The leaderboard displays users ranked by their total Panda Points (PP) in descending order.
    Only Team_Member type users are included in this leaderboard.
    
    **Pagination**:
    - Default page size: 50 entries
    - Maximum page size: 100 entries
    - Results include total count for calculating total pages
    
    **Caching**: Leaderboard data is cached and refreshed every 10 minutes
    """,
    responses={
        200: {
            "description": "Leaderboard retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "entries": [
                            {
                                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                "user_name": "John Doe",
                                "user_type": "Team_Member",
                                "rank": 1,
                                "total_pp": 1250.5,
                                "updated_at": "2024-01-15T10:30:00Z"
                            }
                        ],
                        "total": 50,
                        "page": 1,
                        "page_size": 50
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def get_team_members_leaderboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of entries per page")
):
    """
    Get Team_Member leaderboard with pagination.
    
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of entries per page (max 100)
        
    Returns:
        LeaderboardResponse: Paginated leaderboard entries with metadata
    """
    logger.info(
        f"User {current_user.id} requesting Team_Member leaderboard "
        f"(page={page}, page_size={page_size})"
    )
    
    try:
        # Get leaderboard entries
        entries, total = await LeaderboardService.get_leaderboard(
            db=db,
            user_type=UserType.TEAM_MEMBER,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format with user names
        from sqlalchemy import select
        entry_responses = []
        for entry in entries:
            # Get user name
            result = await db.execute(
                select(User).where(User.id == entry.user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                entry_responses.append(
                    LeaderboardEntryResponse(
                        user_id=entry.user_id,
                        user_name=user.name,
                        user_type=entry.user_type,
                        rank=entry.rank,
                        total_pp=entry.total_pp,
                        updated_at=entry.updated_at
                    )
                )
        
        return LeaderboardResponse(
            entries=entry_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error retrieving Team_Member leaderboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve leaderboard"
        )


@router.get(
    "/ambassadors",
    response_model=LeaderboardResponse,
    summary="Get Ambassador leaderboard",
    description="""
    Retrieve the leaderboard for Ambassadors with pagination.
    
    **Authentication Required**: Yes (Bearer token)
    
    **Permissions**: All authenticated users can view the Ambassador leaderboard
    
    **Validates**: Requirements 6.1, 6.2, 6.5
    
    The leaderboard displays users ranked by their total Panda Points (PP) in descending order.
    Only Ambassador type users are included in this leaderboard.
    
    **Pagination**:
    - Default page size: 50 entries
    - Maximum page size: 100 entries
    - Results include total count for calculating total pages
    
    **Caching**: Leaderboard data is cached and refreshed every 10 minutes
    """,
    responses={
        200: {
            "description": "Leaderboard retrieved successfully"
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def get_ambassadors_leaderboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of entries per page")
):
    """
    Get Ambassador leaderboard with pagination.
    
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number (1-indexed)
        page_size: Number of entries per page (max 100)
        
    Returns:
        LeaderboardResponse: Paginated leaderboard entries with metadata
    """
    logger.info(
        f"User {current_user.id} requesting Ambassador leaderboard "
        f"(page={page}, page_size={page_size})"
    )
    
    try:
        # Get leaderboard entries
        entries, total = await LeaderboardService.get_leaderboard(
            db=db,
            user_type=UserType.AMBASSADOR,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format with user names
        from sqlalchemy import select
        entry_responses = []
        for entry in entries:
            # Get user name
            result = await db.execute(
                select(User).where(User.id == entry.user_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                entry_responses.append(
                    LeaderboardEntryResponse(
                        user_id=entry.user_id,
                        user_name=user.name,
                        user_type=entry.user_type,
                        rank=entry.rank,
                        total_pp=entry.total_pp,
                        updated_at=entry.updated_at
                    )
                )
        
        return LeaderboardResponse(
            entries=entry_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error retrieving Ambassador leaderboard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve leaderboard"
        )


@router.get(
    "/user/{user_id}/rank",
    response_model=UserRankResponse,
    summary="Get user's leaderboard rank",
    description="""
    Retrieve a specific user's rank and points in the leaderboard.
    
    **Authentication Required**: Yes (Bearer token)
    
    **Permissions**: All authenticated users can query any user's rank
    
    **Validates**: Requirements 6.1, 6.2, 6.5
    
    Returns the user's current rank, total PP, and user type. The rank is calculated
    within the user's type group (Team_Member or Ambassador).
    
    **Use Cases**:
    - Display user's own rank on dashboard
    - Compare ranks between users
    - Track rank changes over time
    """,
    responses={
        200: {
            "description": "User rank retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "rank": 5,
                        "total_pp": 750.0,
                        "user_type": "Team_Member"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - Invalid or missing authentication token"
        },
        404: {
            "description": "User not found in leaderboard"
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def get_user_rank(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Get a specific user's leaderboard rank.
    
    **Validates: Requirements 6.1, 6.2, 6.5**
    
    Args:
        user_id: User ID to get rank for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserRankResponse: User's rank and points information
        
    Raises:
        HTTPException: If user not found or not in leaderboard
    """
    logger.info(
        f"User {current_user.id} requesting rank for user {user_id}"
    )
    
    try:
        # Get user's leaderboard entry
        leaderboard_entry = await LeaderboardService.get_user_rank(
            db=db,
            user_id=user_id
        )
        
        if leaderboard_entry is None:
            raise HTTPException(
                status_code=404,
                detail="User not found in leaderboard"
            )
        
        return UserRankResponse(
            user_id=leaderboard_entry.user_id,
            rank=leaderboard_entry.rank,
            total_pp=leaderboard_entry.total_pp,
            user_type=leaderboard_entry.user_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user rank: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user rank"
        )

"""Leaderboard service layer"""
from typing import List, Optional
from sqlalchemy import select, func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.models import LeaderboardCache, User, PointsTransaction, UserType
from app.core.logging import get_logger

logger = get_logger(__name__)


class LeaderboardService:
    """Leaderboard service for business logic"""
    
    @staticmethod
    async def refresh_leaderboard_cache(db: AsyncSession) -> dict:
        """
        Refresh the leaderboard cache by recalculating rankings for all users.
        
        This function:
        1. Calculates total PP for each user from points_transactions
        2. Ranks users in descending order by total_pp within their user_type
        3. Updates the leaderboard_cache table
        
        Args:
            db: Database session
            
        Returns:
            dict: Statistics about the refresh operation
        """
        logger.info("Starting leaderboard cache refresh")
        
        try:
            # Get all active users with their current points
            result = await db.execute(
                select(User).where(User.deleted_at.is_(None))
            )
            users = result.scalars().all()
            
            if not users:
                logger.info("No users found, skipping leaderboard refresh")
                return {"status": "completed", "users_updated": 0}
            
            # Group users by user_type and calculate rankings
            team_members = []
            ambassadors = []
            
            for user in users:
                # Validate user has a valid user_type
                if user.user_type not in [UserType.TEAM_MEMBER, UserType.AMBASSADOR]:
                    logger.warning(
                        f"User {user.id} has invalid user_type: {user.user_type}. Skipping."
                    )
                    continue
                
                user_data = {
                    "user_id": user.id,
                    "user_type": user.user_type.value,
                    "total_pp": float(user.points)
                }
                
                if user.user_type == UserType.TEAM_MEMBER:
                    team_members.append(user_data)
                else:  # Ambassador
                    ambassadors.append(user_data)
            
            # Sort by total_pp in descending order and assign ranks
            team_members.sort(key=lambda x: x["total_pp"], reverse=True)
            ambassadors.sort(key=lambda x: x["total_pp"], reverse=True)
            
            # Assign ranks
            for rank, member in enumerate(team_members, start=1):
                member["rank"] = rank
            
            for rank, ambassador in enumerate(ambassadors, start=1):
                ambassador["rank"] = rank
            
            # Combine all users
            all_ranked_users = team_members + ambassadors
            
            # Update leaderboard_cache table
            updated_count = 0
            for user_data in all_ranked_users:
                # Check if cache entry exists
                result = await db.execute(
                    select(LeaderboardCache).where(
                        LeaderboardCache.user_id == user_data["user_id"]
                    )
                )
                cache_entry = result.scalar_one_or_none()
                
                if cache_entry:
                    # Update existing entry
                    cache_entry.rank = user_data["rank"]
                    cache_entry.total_pp = user_data["total_pp"]
                    cache_entry.user_type = user_data["user_type"]
                    cache_entry.updated_at = datetime.utcnow()
                else:
                    # Create new entry
                    cache_entry = LeaderboardCache(
                        user_id=user_data["user_id"],
                        user_type=user_data["user_type"],
                        rank=user_data["rank"],
                        total_pp=user_data["total_pp"]
                    )
                    db.add(cache_entry)
                
                updated_count += 1
            
            await db.commit()
            
            logger.info(
                f"Leaderboard cache refresh completed. Updated {updated_count} users "
                f"({len(team_members)} Team Members, {len(ambassadors)} Ambassadors)"
            )
            
            return {
                "status": "completed",
                "users_updated": updated_count,
                "team_members": len(team_members),
                "ambassadors": len(ambassadors)
            }
            
        except Exception as e:
            logger.error(f"Error refreshing leaderboard cache: {str(e)}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_leaderboard(
        db: AsyncSession,
        user_type: UserType,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[LeaderboardCache], int]:
        """
        Get leaderboard for a specific user type.
        
        Enforces user_type filtering to prevent cross-type mixing.
        
        Args:
            db: Database session
            user_type: User type to filter by (must be Team_Member or Ambassador)
            page: Page number (1-indexed)
            page_size: Number of entries per page
            
        Returns:
            tuple: (list of leaderboard entries, total count)
            
        Raises:
            ValueError: If user_type is not a valid UserType enum value
        """
        # Validate user_type is a valid enum value
        if not isinstance(user_type, UserType):
            raise ValueError(
                f"Invalid user_type. Must be UserType.TEAM_MEMBER or UserType.AMBASSADOR"
            )
        
        # Build query with strict user_type filtering
        query = select(LeaderboardCache).where(
            LeaderboardCache.user_type == user_type.value
        )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(LeaderboardCache.rank.asc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        entries = result.scalars().all()
        
        return list(entries), total
    
    @staticmethod
    async def get_user_rank(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[LeaderboardCache]:
        """
        Get a specific user's leaderboard rank.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            LeaderboardCache: User's leaderboard entry or None if not found
        """
        result = await db.execute(
            select(LeaderboardCache).where(LeaderboardCache.user_id == user_id)
        )
        return result.scalar_one_or_none()

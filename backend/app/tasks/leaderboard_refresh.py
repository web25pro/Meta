"""Leaderboard cache refresh background task"""
from app.celery_app import celery_app
from app.core.logging import get_logger
from app.core.database import async_session_maker
from app.services.leaderboard_service import LeaderboardService

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.leaderboard_refresh.refresh_leaderboard_cache")
def refresh_leaderboard_cache():
    """
    Refresh the leaderboard cache by recalculating rankings.
    
    This task runs every 10 minutes to update the leaderboard_cache table
    with current rankings based on total PP for each user type.
    
    Returns:
        dict: Statistics about the refresh operation
    """
    logger.info("Starting leaderboard cache refresh job")
    
    try:
        # Create async session and run the refresh
        import asyncio
        
        async def run_refresh():
            async with async_session_maker() as db:
                result = await LeaderboardService.refresh_leaderboard_cache(db)
                return result
        
        # Run the async function
        result = asyncio.run(run_refresh())
        
        logger.info(
            f"Leaderboard cache refresh completed: {result['users_updated']} users updated "
            f"({result.get('team_members', 0)} Team Members, {result.get('ambassadors', 0)} Ambassadors)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in leaderboard cache refresh job: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "users_updated": 0
        }

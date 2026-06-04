"""Redis client configuration and connection pooling"""
from typing import Optional
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection pool"""
    global _redis_pool, _redis_client
    
    _redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_POOL_SIZE,
        decode_responses=True,
    )
    
    _redis_client = redis.Redis(connection_pool=_redis_pool)


async def close_redis() -> None:
    """Close Redis connection pool"""
    global _redis_pool, _redis_client
    
    if _redis_client:
        await _redis_client.close()
    
    if _redis_pool:
        await _redis_pool.disconnect()


def get_redis() -> redis.Redis:
    """
    Get Redis client instance.
    
    Returns:
        redis.Redis: Redis client
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client

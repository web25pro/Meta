"""Rate limiting middleware using Redis sliding window algorithm"""
import time
from typing import Callable, Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.core.redis import get_redis
from app.core.security import verify_token

logger = get_logger(__name__)


class RateLimitConfig:
    """Rate limit configuration for different endpoint types"""
    
    # General API rate limit: 100 requests/minute per user
    GENERAL_API_LIMIT = 100
    GENERAL_API_WINDOW = 60  # seconds
    
    # File upload rate limit: 10 uploads/minute per user
    FILE_UPLOAD_LIMIT = 10
    FILE_UPLOAD_WINDOW = 60  # seconds
    
    # Leaderboard query rate limit: 30 requests/minute per user
    LEADERBOARD_LIMIT = 30
    LEADERBOARD_WINDOW = 60  # seconds


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


def extract_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extract user_id from JWT token in Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    try:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            token_data = verify_token(token)
            if token_data:
                return token_data.user_id
    except Exception:
        # Silently fail - unauthenticated requests will use IP-based limiting
        pass
    return None


def get_rate_limit_key(user_id: Optional[str], client_ip: str, endpoint_type: str) -> str:
    """
    Generate Redis key for rate limiting.
    
    Args:
        user_id: User ID if authenticated
        client_ip: Client IP address
        endpoint_type: Type of endpoint (general, upload, leaderboard)
        
    Returns:
        str: Redis key for rate limiting
    """
    identifier = user_id if user_id else f"ip:{client_ip}"
    return f"rate_limit:{endpoint_type}:{identifier}"


def get_endpoint_type(path: str, method: str) -> str:
    """
    Determine endpoint type based on path and method.
    
    Args:
        path: Request path
        method: HTTP method
        
    Returns:
        str: Endpoint type (general, upload, leaderboard)
    """
    # File upload endpoints
    if "/submissions" in path and method == "POST":
        return "upload"
    
    # Leaderboard endpoints
    if "/leaderboard" in path:
        return "leaderboard"
    
    # Default to general API
    return "general"


def get_rate_limit_config(endpoint_type: str) -> tuple[int, int]:
    """
    Get rate limit configuration for endpoint type.
    
    Args:
        endpoint_type: Type of endpoint (general, upload, leaderboard)
        
    Returns:
        tuple[int, int]: (limit, window_seconds)
    """
    if endpoint_type == "upload":
        return (RateLimitConfig.FILE_UPLOAD_LIMIT, RateLimitConfig.FILE_UPLOAD_WINDOW)
    elif endpoint_type == "leaderboard":
        return (RateLimitConfig.LEADERBOARD_LIMIT, RateLimitConfig.LEADERBOARD_WINDOW)
    else:
        return (RateLimitConfig.GENERAL_API_LIMIT, RateLimitConfig.GENERAL_API_WINDOW)


async def check_rate_limit(
    redis_client,
    key: str,
    limit: int,
    window: int
) -> tuple[bool, int, int]:
    """
    Check if request is within rate limit using sliding window algorithm.
    
    Algorithm:
    1. Remove timestamps older than the window
    2. Count remaining timestamps
    3. If count < limit, allow request and add timestamp
    4. If count >= limit, deny request
    
    Args:
        redis_client: Redis client instance
        key: Redis key for rate limiting
        limit: Maximum number of requests allowed
        window: Time window in seconds
        
    Returns:
        tuple[bool, int, int]: (allowed, remaining, retry_after)
    """
    now = time.time()
    window_start = now - window
    
    # Use Redis pipeline for atomic operations
    pipe = redis_client.pipeline()
    
    # Remove old timestamps outside the window
    pipe.zremrangebyscore(key, 0, window_start)
    
    # Count current requests in window
    pipe.zcard(key)
    
    # Execute pipeline
    results = await pipe.execute()
    current_count = results[1]
    
    if current_count < limit:
        # Allow request - add timestamp
        await redis_client.zadd(key, {str(now): now})
        await redis_client.expire(key, window)
        
        remaining = limit - current_count - 1
        return (True, remaining, 0)
    else:
        # Deny request - calculate retry_after
        # Get oldest timestamp in window
        oldest_timestamps = await redis_client.zrange(key, 0, 0, withscores=True)
        if oldest_timestamps:
            oldest_time = oldest_timestamps[0][1]
            retry_after = int(oldest_time + window - now) + 1
        else:
            retry_after = window
        
        return (False, 0, retry_after)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on API endpoints.
    
    Features:
    - Sliding window rate limiting algorithm
    - Different rate limits for different endpoint types
    - Per-user rate limiting (authenticated requests)
    - Per-IP rate limiting (unauthenticated requests)
    - Returns 429 Too Many Requests with Retry-After header
    """
    
    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and enforce rate limiting.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response: FastAPI response object
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        try:
            # Get Redis client
            redis_client = get_redis()
            
            # Extract user_id and client_ip
            user_id = extract_user_id_from_request(request)
            client_ip = request.client.host if request.client else "unknown"
            
            # Determine endpoint type
            endpoint_type = get_endpoint_type(request.url.path, request.method)
            
            # Get rate limit configuration
            limit, window = get_rate_limit_config(endpoint_type)
            
            # Generate rate limit key
            key = get_rate_limit_key(user_id, client_ip, endpoint_type)
            
            # Check rate limit
            allowed, remaining, retry_after = await check_rate_limit(
                redis_client, key, limit, window
            )
            
            if not allowed:
                # Rate limit exceeded
                logger.warning(
                    "Rate limit exceeded",
                    extra={
                        "user_id": user_id,
                        "client_ip": client_ip,
                        "endpoint_type": endpoint_type,
                        "path": request.url.path,
                        "method": request.method,
                        "limit": limit,
                        "window": window,
                        "retry_after": retry_after,
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "success": False,
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded. Maximum {limit} requests per {window} seconds allowed.",
                            "details": {
                                "limit": limit,
                                "window": window,
                                "retry_after": retry_after,
                            }
                        }
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + retry_after)),
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + window))
            
            return response
            
        except Exception as e:
            # Log error but don't block request
            logger.error(
                "Rate limiting error",
                extra={
                    "error": str(e),
                    "path": request.url.path,
                    "method": request.method,
                },
                exc_info=True
            )
            
            # Allow request to proceed if rate limiting fails
            return await call_next(request)

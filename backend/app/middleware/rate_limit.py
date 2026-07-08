"""Sliding-window rate limiting middleware (in-memory, no Redis dependency)"""
import time
from collections import defaultdict
from typing import Callable, Dict, List, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding-window rate limiter.

    Tracks request timestamps per client IP and enforces configurable
    limits for different endpoint groups.

    Limits (per minute):
        - Auth endpoints (login, register, refresh): RATE_LIMIT_AUTH_PER_MINUTE
        - File uploads: RATE_LIMIT_UPLOAD_PER_MINUTE
        - All other endpoints: RATE_LIMIT_DEFAULT_PER_MINUTE
    """

    # Endpoint prefixes that get the stricter auth limit
    AUTH_PREFIXES = (
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/community/login",
        "/api/v1/community/register",
        "/api/v1/community/verify-email",
        "/api/v1/community/password-reset",
    )

    # Endpoint prefixes that get the upload limit
    UPLOAD_PREFIXES = (
        "/api/v1/files",
        "/api/v1/submissions",
    )

    def __init__(
        self,
        app: ASGIApp,
        default_per_minute: int = 100,
        auth_per_minute: int = 20,
        upload_per_minute: int = 10,
    ):
        super().__init__(app)
        self.default_per_minute = default_per_minute
        self.auth_per_minute = auth_per_minute
        self.upload_per_minute = upload_per_minute
        # {ip: [(timestamp, path), ...]}
        self._requests: Dict[str, List[Tuple[float, str]]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For for reverse proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_limit(self, path: str) -> Tuple[int, str]:
        """Return (limit_per_minute, group_name) for the given path."""
        for prefix in self.AUTH_PREFIXES:
            if path.startswith(prefix):
                return self.auth_per_minute, "auth"
        for prefix in self.UPLOAD_PREFIXES:
            if path.startswith(prefix):
                return self.upload_per_minute, "upload"
        return self.default_per_minute, "default"

    def _cleanup(self, ip: str, window_start: float) -> None:
        """Remove expired entries for an IP."""
        self._requests[ip] = [
            (ts, p) for ts, p in self._requests[ip] if ts > window_start
        ]
        if not self._requests[ip]:
            del self._requests[ip]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health/root endpoints
        path = request.url.path
        if path in ("/", "/health"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        limit, group = self._get_limit(path)
        now = time.time()
        window_start = now - 60.0  # 1-minute sliding window

        # Cleanup old entries
        self._cleanup(ip, window_start)

        # Count requests in the current window
        request_count = len(self._requests[ip])

        if request_count >= limit:
            retry_after = int(60 - (now - self._requests[ip][0][0])) + 1
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": ip,
                    "group": group,
                    "path": path,
                    "request_count": request_count,
                    "limit": limit,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "details": {
                            "limit": limit,
                            "window": "60s",
                            "retry_after": retry_after,
                        },
                    },
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._requests[ip].append((now, path))

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - request_count - 1))
        response.headers["X-RateLimit-Reset"] = str(int(now + 60))

        return response

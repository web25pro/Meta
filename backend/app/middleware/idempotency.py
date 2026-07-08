"""Idempotency middleware to prevent duplicate submissions"""
import hashlib
import time
from typing import Callable, Dict, Optional, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)

# Methods that require idempotency keys
IDEMPOTENT_METHODS = {"POST"}

# TTL for idempotency keys (seconds)
IDEMPOTENCY_TTL = 300  # 5 minutes

# Endpoints exempt from idempotency requirements
IDEMPOTENCY_EXEMPT_PREFIXES = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/v1/community/login",
    "/api/v1/community/register",
    "/api/v1/community/verify-email",
    "/api/v1/community/password-reset",
    "/api/v1/public",
    "/",
    "/health",
}

IDEMPOTENCY_HEADER = "x-idempotency-key"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware for duplicate submission prevention.

    Flow:
    1. On POST requests, require an `X-Idempotency-Key` header.
    2. Store the key + request body hash with a 5-minute TTL.
    3. If the same key is seen with the same body → return cached response.
    4. If the same key is seen with a different body → return 409 Conflict.
    5. Keys auto-expire after TTL to prevent memory leaks.

    This prevents accidental double-submits from users clicking twice,
    network retries, or frontend bugs.
    """

    def __init__(self, app: ASGIApp, ttl: int = IDEMPOTENCY_TTL):
        super().__init__(app)
        self.ttl = ttl
        # {key: (expiry_time, body_hash, status_code, response_body)}
        self._store: Dict[str, Tuple[float, str, int, bytes]] = {}

    def _cleanup_expired(self) -> None:
        """Remove expired entries. Called on every request (cheap for small stores)."""
        now = time.time()
        expired = [k for k, (exp, *_) in self._store.items() if exp < now]
        for k in expired:
            del self._store[k]

    def _is_exempt(self, request: Request) -> bool:
        """Check if the request is exempt from idempotency requirements."""
        if request.method not in IDEMPOTENT_METHODS:
            return True

        path = request.url.path
        for prefix in IDEMPOTENCY_EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _hash_body(self, body: bytes) -> str:
        """Hash the request body for comparison."""
        return hashlib.sha256(body).hexdigest()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip exempt endpoints
        if self._is_exempt(request):
            return await call_next(request)

        # Cleanup expired entries periodically
        self._cleanup_expired()

        # Get idempotency key
        key = request.headers.get(IDEMPOTENCY_HEADER)
        if not key:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "error": {
                        "code": "IDEMPOTENCY_KEY_REQUIRED",
                        "message": "X-Idempotency-Key header is required for POST requests.",
                        "details": {},
                    },
                },
            )

        # Read request body for hashing
        body = await request.body()
        body_hash = self._hash_body(body)

        # Check if we've seen this key before
        if key in self._store:
            stored_expiry, stored_hash, stored_status, stored_body = self._store[key]

            if stored_hash == body_hash:
                # Same request — return cached response
                logger.info(
                    "Idempotency replay",
                    extra={"key": key, "path": request.url.path},
                )
                return JSONResponse(
                    status_code=stored_status,
                    content=stored_body.decode("utf-8") if stored_body else None,
                    headers={"X-Idempotency-Replay": "true"},
                )
            else:
                # Same key, different body — conflict
                logger.warning(
                    "Idempotency key conflict",
                    extra={"key": key, "path": request.url.path},
                )
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "success": False,
                        "error": {
                            "code": "IDEMPOTENCY_CONFLICT",
                            "message": "This idempotency key was already used with a different request body.",
                            "details": {},
                        },
                    },
                )

        # Store the key and process the request
        # We need to reconstruct the body stream since we consumed it
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive  # noqa: SLF001

        response = await call_next(request)

        # Cache successful responses only
        if 200 <= response.status_code < 300:
            response_body = b""
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    response_body += chunk.encode("utf-8")
                else:
                    response_body += chunk

            self._store[key] = (
                time.time() + self.ttl,
                body_hash,
                response.status_code,
                response_body,
            )

            # Return a new response with the same body
            from starlette.responses import Response as StarletteResponse

            return StarletteResponse(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        return response

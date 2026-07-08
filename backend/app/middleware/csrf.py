"""CSRF protection middleware using double-submit cookie pattern"""
import secrets
from typing import Callable, Set

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger

logger = get_logger(__name__)

# Safe methods that do not require CSRF validation
SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

# Public endpoints that skip CSRF (auth flows that don't have a prior GET to set the cookie)
CSRF_EXEMPT_PREFIXES: Set[str] = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/community/login",
    "/api/v1/community/register",
    "/api/v1/community/verify-email",
    "/api/v1/community/password-reset",
    "/api/v1/public",
    "/",
    "/health",
}

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double-submit cookie CSRF protection.

    Flow:
    1. On every response, set a `csrf_token` cookie (if not already present).
    2. On every mutating request (POST/PUT/DELETE/PATCH), validate that the
       `X-CSRF-Token` header matches the cookie value.
    3. Exempt safe methods (GET/HEAD/OPTIONS) and public auth endpoints.

    The cookie is NOT HttpOnly so the frontend JS can read it and echo it
    back in the header. The security relies on the fact that an attacker
    on a different origin cannot read cookies set by this domain.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    def _is_exempt(self, request: Request) -> bool:
        """Check if the request is exempt from CSRF validation."""
        # Safe methods are always exempt
        if request.method in SAFE_METHODS:
            return True

        path = request.url.path
        for prefix in CSRF_EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _get_or_create_csrf_token(self, request: Request) -> str:
        """Get existing CSRF token from cookie, or generate a new one."""
        token = request.cookies.get(CSRF_COOKIE_NAME)
        if token:
            return token
        return secrets.token_urlsafe(32)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate CSRF on mutating requests
        if not self._is_exempt(request):
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)

            if not cookie_token or not header_token:
                logger.warning(
                    "CSRF validation failed: missing token",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "has_cookie": bool(cookie_token),
                        "has_header": bool(header_token),
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "success": False,
                        "error": {
                            "code": "CSRF_FAILED",
                            "message": "CSRF token missing. Include X-CSRF-Token header.",
                            "details": {},
                        },
                    },
                )

            if not secrets.compare_digest(cookie_token, header_token):
                logger.warning(
                    "CSRF validation failed: token mismatch",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "success": False,
                        "error": {
                            "code": "CSRF_FAILED",
                            "message": "CSRF token mismatch.",
                            "details": {},
                        },
                    },
                )

        # Process the request
        response = await call_next(request)

        # Set CSRF cookie on every response (ensure it's always available)
        csrf_token = self._get_or_create_csrf_token(request)
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            max_age=86400,  # 1 day
            httponly=False,  # JS must be able to read it
            samesite="lax",
            secure=True,
            path="/",
        )

        return response

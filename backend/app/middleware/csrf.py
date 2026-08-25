"""CSRF protection middleware using double-submit cookie pattern.

Implemented as a **pure ASGI middleware** (not BaseHTTPMiddleware) so that
short-circuit responses (403 on CSRF failure) don't trigger the
"No response returned" RuntimeError or ASGI body-draining crashes that
BaseHTTPMiddleware is prone to when ``call_next`` is never called.
"""
import secrets
from typing import Set

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Safe methods that do not require CSRF validation
SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

# Public endpoints that skip CSRF (auth flows that don't have a prior GET to set the cookie)
CSRF_EXEMPT_PREFIXES: Set[str] = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/community/login",
    "/api/v1/community/register",
    "/api/v1/admin",
    "/api/v1/public",
    "/health",
}

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"

# Cookie attributes (serialised into the Set-Cookie header)
_SECURE = settings.APP_ENV.lower() not in {"development", "dev", "test", "testing", "local"}


def _build_cookie_header(token: str) -> str:
    """Build a Set-Cookie header value for the CSRF token."""
    parts = [
        f"{CSRF_COOKIE_NAME}={token}",
        "Path=/",
        "Max-Age=86400",  # 1 day
        "SameSite=Lax",
    ]
    if _SECURE:
        parts.append("Secure")
    return "; ".join(parts)


class CSRFMiddleware:
    """
    Double-submit cookie CSRF protection (pure ASGI).

    Flow:
    1. On every response, set a ``csrf_token`` cookie (if not already present).
    2. On every mutating request (POST/PUT/DELETE/PATCH), validate that the
       ``X-CSRF-Token`` header matches the cookie value.
    3. Exempt safe methods (GET/HEAD/OPTIONS) and public auth endpoints.

    The cookie is NOT HttpOnly so the frontend JS can read it and echo it
    back in the header. The security relies on the fact that an attacker
    on a different origin cannot read cookies set by this domain.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    # ── Helpers (static, no self needed for logic) ────────────────────────

    @staticmethod
    def _is_exempt(scope: Scope) -> bool:
        """Check if the request is exempt from CSRF validation."""
        if scope.get("method", "GET") in SAFE_METHODS:
            return True
        path = scope.get("path", "")
        return any(path.startswith(prefix) for prefix in CSRF_EXEMPT_PREFIXES)

    @staticmethod
    def _get_csrf_token(scope: Scope) -> str | None:
        """Extract the existing csrf_token from request cookies, if present."""
        for raw in scope.get("headers", []):
            if raw[0] == b"cookie":
                for part in raw[1].decode("latin-1").split(";"):
                    name, _, value = part.strip().partition("=")
                    if name == CSRF_COOKIE_NAME:
                        return value
        return None

    @staticmethod
    def _get_header(scope: Scope, name: str) -> str | None:
        """Extract a header value from the ASGI scope (case-insensitive lookup)."""
        name_bytes = name.encode("latin-1")
        for raw in scope.get("headers", []):
            if raw[0] == name_bytes:
                return raw[1].decode("latin-1")
        return None

    def _wrap_send(self, send: Send, csrf_token: str) -> Send:
        """Wrap the ASGI ``send`` callable to inject the CSRF Set-Cookie header."""
        cookie_header = _build_cookie_header(csrf_token).encode("latin-1")
        injected = False

        async def send_wrapper(message):
            nonlocal injected
            if message["type"] == "http.response.start" and not injected:
                injected = True
                headers = list(message.get("headers", []))
                headers.append((b"set-cookie", cookie_header))
                message = {**message, "headers": headers}
            await send(message)

        return send_wrapper

    # ── ASGI entry point ──────────────────────────────────────────────────

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Only intercept HTTP — pass websockets through unchanged.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # If CSRF is globally disabled (e.g. test environment), pass through.
        if not settings.CSRF_ENABLED:
            await self.app(scope, receive, send)
            return

        # Exempt requests: run inner app but still set the CSRF cookie.
        if self._is_exempt(scope):
            token = self._get_csrf_token(scope) or secrets.token_urlsafe(32)
            await self.app(scope, receive, self._wrap_send(send, token))
            return

        # ── CSRF validation on mutating requests ──────────────────────────
        cookie_token = self._get_csrf_token(scope)
        header_token = self._get_header(scope, CSRF_HEADER_NAME)

        # Always ensure a token exists so the next GET can pick it up.
        csrf_token = cookie_token or secrets.token_urlsafe(32)
        wrapped_send = self._wrap_send(send, csrf_token)

        if not cookie_token or not header_token:
            logger.warning(
                "CSRF validation failed: missing token",
                extra={
                    "path": scope.get("path", ""),
                    "method": scope.get("method", ""),
                    "has_cookie": bool(cookie_token),
                    "has_header": bool(header_token),
                },
            )
            response = JSONResponse(
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
            await response(scope, receive, wrapped_send)
            return

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(
                "CSRF validation failed: token mismatch",
                extra={
                    "path": scope.get("path", ""),
                    "method": scope.get("method", ""),
                },
            )
            response = JSONResponse(
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
            await response(scope, receive, wrapped_send)
            return

        # ── Validation passed — run inner app ─────────────────────────────
        await self.app(scope, receive, wrapped_send)

"""Security headers middleware"""
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds standard security headers to every response.

    Headers:
        - X-Content-Type-Options: nosniff — prevents MIME-type sniffing
        - X-Frame-Options: DENY — prevents clickjacking
        - Strict-Transport-Security — enforces HTTPS (HSTS)
        - X-XSS-Protection: 0 — disables legacy XSS filter (rely on CSP)
        - Referrer-Policy: strict-origin-when-cross-origin
        - Permissions-Policy — restricts browser features
        - Content-Security-Policy — basic CSP for API responses
    """

    def __init__(self, app: ASGIApp, hsts_max_age: int = 31536000):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.hsts_max_age}; includeSubDomains"
        )
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"

        return response

"""Database-backed idempotency for mutating API requests."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.security import verify_token
from app.models import IdempotencyKey

logger = get_logger(__name__)

IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
IDEMPOTENCY_TTL = 300
IDEMPOTENCY_HEADER = "x-idempotency-key"
IDEMPOTENCY_EXEMPT_PREFIXES = {
    "/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/logout",
    "/api/v1/community/login", "/api/v1/community/register",
    "/api/v1/community/verify-email", "/api/v1/community/password-reset",
    "/api/v1/community/resend-verification",
    "/api/v1/admin", "/api/v1/public", "/health",
}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Require and persist idempotency keys for authenticated mutations.

    A short-lived ``processing`` row is claimed before the handler runs. A
    second request with the same user/key is replayed after completion, or gets
    a conflict while the original request is still executing. Expired rows are
    reclaimable, covering crashes between claim and response storage.
    """

    def __init__(self, app: ASGIApp, ttl: int = IDEMPOTENCY_TTL):
        super().__init__(app)
        self.ttl = ttl

    def _is_exempt(self, request: Request) -> bool:
        if request.method not in IDEMPOTENT_METHODS:
            return True
        return any(request.url.path.startswith(prefix) for prefix in IDEMPOTENCY_EXEMPT_PREFIXES)

    @staticmethod
    def _user_id(request: Request) -> uuid.UUID | None:
        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            return None
        token = verify_token(authorization[7:].strip())
        if not token:
            return None
        try:
            return uuid.UUID(token.user_id)
        except ValueError:
            return None

    @staticmethod
    async def _body(request: Request) -> bytes:
        body = await request.body()
        body_replayed = False

        async def receive():
            """Replay the body once, then signal end-of-stream.

            Starlette may call ``receive`` again while it finishes a response.
            Returning the same ``http.request`` event on every call causes an
            ``Unexpected message received: http.request`` runtime error after
            otherwise successful mutations such as quest completion.
            """
            nonlocal body_replayed
            if not body_replayed:
                body_replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        request._receive = receive  # noqa: SLF001
        return body

    @staticmethod
    def _error(code: str, message: str, response_status: int) -> JSONResponse:
        return JSONResponse(
            status_code=response_status,
            content={"success": False, "error": {"code": code, "message": message, "details": {}}},
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.IDEMPOTENCY_ENABLED or self._is_exempt(request):
            return await call_next(request)

        key = request.headers.get(IDEMPOTENCY_HEADER, "").strip()
        if not key or len(key) > 255:
            return self._error(
                "IDEMPOTENCY_KEY_REQUIRED",
                "A valid X-Idempotency-Key header is required for mutating requests.",
                status.HTTP_400_BAD_REQUEST,
            )

        body = await self._body(request)
        body_hash = hashlib.sha256(body).hexdigest()
        user_id = self._user_id(request)

        # Let the normal auth dependency produce the correct 401 when a token
        # is absent/invalid; there is no user scope to persist in that case.
        if user_id is None:
            return await call_next(request)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl)
        record: IdempotencyKey | None = None

        async with AsyncSessionLocal() as db:
            await db.execute(delete(IdempotencyKey).where(IdempotencyKey.expires_at <= now))
            await db.commit()
            record = await db.scalar(
                select(IdempotencyKey).where(
                    IdempotencyKey.user_id == user_id,
                    IdempotencyKey.key == key,
                )
            )
            if record:
                if record.body_hash != body_hash or record.method != request.method or record.path != request.url.path:
                    return self._error(
                        "IDEMPOTENCY_CONFLICT",
                        "This idempotency key was already used with a different request.",
                        status.HTTP_409_CONFLICT,
                    )
                if record.processing or record.status_code is None:
                    return self._error(
                        "IDEMPOTENCY_IN_PROGRESS",
                        "The original request is still being processed.",
                        status.HTTP_409_CONFLICT,
                    )
                return JSONResponse(
                    status_code=record.status_code,
                    content=record.response_json,
                    headers={"X-Idempotency-Replay": "true"},
                )

            record = IdempotencyKey(
                user_id=user_id,
                key=key,
                method=request.method,
                path=request.url.path,
                body_hash=body_hash,
                processing=True,
                expires_at=expires_at,
            )
            db.add(record)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                return self._error(
                    "IDEMPOTENCY_IN_PROGRESS",
                    "The original request is still being processed.",
                    status.HTTP_409_CONFLICT,
                )

        try:
            response = await call_next(request)
            if not 200 <= response.status_code < 300:
                async with AsyncSessionLocal() as db:
                    await db.execute(delete(IdempotencyKey).where(IdempotencyKey.id == record.id))
                    await db.commit()
                return response

            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk.encode() if isinstance(chunk, str) else chunk
            try:
                response_json = json.loads(response_body.decode("utf-8")) if response_body else None
            except (UnicodeDecodeError, json.JSONDecodeError):
                response_json = {"_raw": response_body.decode("utf-8", errors="replace")}

            async with AsyncSessionLocal() as db:
                stored = await db.scalar(select(IdempotencyKey).where(IdempotencyKey.id == record.id))
                if stored:
                    stored.status_code = response.status_code
                    stored.response_json = response_json
                    stored.response_content_type = response.headers.get("content-type")
                    stored.processing = False
                    await db.commit()

            return StarletteResponse(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception:
            async with AsyncSessionLocal() as db:
                await db.execute(delete(IdempotencyKey).where(IdempotencyKey.id == record.id))
                await db.commit()
            raise

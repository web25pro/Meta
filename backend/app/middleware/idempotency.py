"""Database-backed idempotency for mutating API requests.

Implemented as a **pure ASGI middleware** (not BaseHTTPMiddleware) so that
exceptions from the inner app are handled cleanly by ExceptionMiddleware
(which sits *inside* this middleware) and never surface as the
"No response returned" RuntimeError that BaseHTTPMiddleware produces
when ``call_next`` raises.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from starlette.types import ASGIApp, Receive, Scope, Send

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
    "/api/v1/community/password-reset",
    "/api/v1/admin", "/api/v1/public", "/health",
}

# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #


def _error_response(code: str, message: str, response_status: int) -> JSONResponse:
    return JSONResponse(
        status_code=response_status,
        content={"success": False, "error": {"code": code, "message": message, "details": {}}},
    )


def _is_exempt(scope: Scope) -> bool:
    method = scope.get("method", "GET")
    if method not in IDEMPOTENT_METHODS:
        return True
    path = scope.get("path", "")
    return any(path.startswith(prefix) for prefix in IDEMPOTENCY_EXEMPT_PREFIXES)


def _get_header(scope: Scope, name: str) -> str | None:
    """Return a header value from the ASGI scope (case-insensitive)."""
    name_lower = name.lower()
    for raw_key, raw_val in scope.get("headers", []):
        if raw_key.decode("latin-1").lower() == name_lower:
            return raw_val.decode("latin-1")
    return None


def _get_cookie(scope: Scope, name: str) -> str | None:
    """Extract a cookie value from the request headers."""
    cookie_header = _get_header(scope, "cookie")
    if not cookie_header:
        return None
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == name:
            return v
    return None


def _user_id_from_scope(scope: Scope) -> str | None:
    """Extract user_id from the JWT in the Authorization header."""
    auth = _get_header(scope, "authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        token_data = verify_token(token)
        return token_data.user_id if token_data else None
    except Exception:
        return None


async def _read_body(receive: Receive) -> bytes:
    """Read the complete request body from the ASGI receive channel."""
    body = b""
    more = True
    while more:
        message = await receive()
        if message["type"] == "http.request":
            body += message.get("body", b"")
            more = message.get("more_body", False)
        elif message["type"] == "http.disconnect":
            break
    return body


def _make_replay_receive(body: bytes) -> Receive:
    """Create a receive callable that replays the buffered body once.

    ASGI applications may call ``receive`` again after consuming the request
    body while they wait for a client disconnect.  At that point the body has
    already been fully replayed, so the only valid event is
    ``http.disconnect``.  Returning another ``http.request`` here violates
    Starlette's receive contract and causes BaseHTTPMiddleware to raise
    ``RuntimeError: Unexpected message received: http.request``.
    """
    sent = False

    async def replay_receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return replay_receive


async def _send_response(response: JSONResponse, scope: Scope, receive: Receive, send: Send):
    """Send a JSONResponse through the ASGI send channel."""
    await response(scope, receive, send)


async def _delete_idempotency_record(record_id: uuid.UUID):
    """Best-effort cleanup of an idempotency record."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(IdempotencyKey).where(IdempotencyKey.id == record_id))
            await db.commit()
    except Exception:
        logger.warning("Failed to delete idempotency record %s", record_id, exc_info=True)


# --------------------------------------------------------------------------- #
#  Middleware
# --------------------------------------------------------------------------- #


class IdempotencyMiddleware:
    """Require and persist idempotency keys for authenticated mutations.

    Pure ASGI implementation — no BaseHTTPMiddleware, so no "No response
    returned" RuntimeError.  Exceptions from the inner app are caught by
    ExceptionMiddleware (which sits *inside* this middleware) and produce
    proper JSON responses that flow back through ``send`` cleanly.
    """

    def __init__(self, app: ASGIApp, ttl: int = IDEMPOTENCY_TTL):
        self.app = app
        self.ttl = ttl

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Only intercept HTTP — pass websockets through unchanged.
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # If idempotency is globally disabled or request is exempt, pass through.
        if not settings.IDEMPOTENCY_ENABLED or _is_exempt(scope):
            await self.app(scope, receive, send)
            return

        # ── Validate idempotency key header ────────────────────────────────
        key = (_get_header(scope, IDEMPOTENCY_HEADER) or "").strip()
        if not key or len(key) > 255:
            resp = _error_response(
                "IDEMPOTENCY_KEY_REQUIRED",
                "A valid X-Idempotency-Key header is required for mutating requests.",
                status.HTTP_400_BAD_REQUEST,
            )
            await resp(scope, receive, send)
            return

        # ── Read & buffer the request body ─────────────────────────────────
        try:
            body = await _read_body(receive)
        except Exception:
            logger.warning("Failed to read request body for idempotency", exc_info=True)
            # Can't buffer body — just pass through without idempotency.
            await self.app(scope, receive, send)
            return

        body_hash = hashlib.sha256(body).hexdigest()
        replay_receive = _make_replay_receive(body)

        # ── Extract user_id from JWT ───────────────────────────────────────
        user_id = _user_id_from_scope(scope)
        if user_id is None:
            # No valid token — let the auth dependency produce the 401.
            await self.app(scope, replay_receive, send)
            return

        # ── Database: check for existing key ───────────────────────────────
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.ttl)
        record: IdempotencyKey | None = None

        try:
            async with AsyncSessionLocal() as db:
                # Purge expired keys.
                await db.execute(delete(IdempotencyKey).where(IdempotencyKey.expires_at <= now))
                await db.commit()

                record = await db.scalar(
                    select(IdempotencyKey).where(
                        IdempotencyKey.user_id == user_id,
                        IdempotencyKey.key == key,
                    )
                )

                if record:
                    # Key already exists — check for conflict or replay.
                    if (
                        record.body_hash != body_hash
                        or record.method != scope.get("method", "")
                        or record.path != scope.get("path", "")
                    ):
                        resp = _error_response(
                            "IDEMPOTENCY_CONFLICT",
                            "This idempotency key was already used with a different request.",
                            status.HTTP_409_CONFLICT,
                        )
                        await resp(scope, receive, send)
                        return

                    if record.processing or record.status_code is None:
                        resp = _error_response(
                            "IDEMPOTENCY_IN_PROGRESS",
                            "The original request is still being processed.",
                            status.HTTP_409_CONFLICT,
                        )
                        await resp(scope, receive, send)
                        return

                    # Replay the cached response.
                    replay_resp = JSONResponse(
                        status_code=record.status_code,
                        content=record.response_json,
                        headers={"X-Idempotency-Replay": "true"},
                    )
                    await replay_resp(scope, receive, send)
                    return

                # Create a new processing record.
                record = IdempotencyKey(
                    user_id=user_id,
                    key=key,
                    method=scope.get("method", ""),
                    path=scope.get("path", ""),
                    body_hash=body_hash,
                    processing=True,
                    expires_at=expires_at,
                )
                db.add(record)
                try:
                    await db.commit()
                except IntegrityError:
                    await db.rollback()
                    resp = _error_response(
                        "IDEMPOTENCY_IN_PROGRESS",
                        "The original request is still being processed.",
                        status.HTTP_409_CONFLICT,
                    )
                    await resp(scope, receive, send)
                    return
        except Exception:
            # DB error during idempotency check — degrade gracefully.
            logger.warning("Idempotency DB check failed, forwarding without idempotency", exc_info=True)
            await self.app(scope, replay_receive, send)
            return

        # ── Call the inner app and capture the response ────────────────────
        # We wrap `send` to intercept http.response.start and http.response.body
        # messages so we can store the response for future replays.
        captured_status: int | None = None
        captured_headers: list[tuple[bytes, bytes]] = []
        captured_body: bytes = b""
        response_started = False

        async def send_wrapper(message):
            nonlocal captured_status, captured_headers, captured_body, response_started

            if message["type"] == "http.response.start":
                response_started = True
                captured_status = message.get("status", 500)
                captured_headers = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                captured_body += message.get("body", b"")

            await send(message)

        try:
            await self.app(scope, replay_receive, send_wrapper)
        except Exception:
            # Inner app raised — ExceptionMiddleware should have caught it,
            # but if something slipped through, clean up and send a 500.
            logger.error("Idempotency: inner app raised unhandled exception", exc_info=True)
            await _delete_idempotency_record(record.id)
            if not response_started:
                resp = JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": {
                            "code": "INTERNAL_SERVER_ERROR",
                            "message": "An unexpected error occurred.",
                            "details": {},
                        },
                    },
                )
                await resp(scope, receive, send)
            return

        # ── Store the response for future replays ──────────────────────────
        if captured_status is not None:
            # Parse the captured body as JSON.
            try:
                response_json = json.loads(captured_body.decode("utf-8")) if captured_body else None
            except (UnicodeDecodeError, json.JSONDecodeError):
                response_json = {"_raw": captured_body.decode("utf-8", errors="replace")}

            # Only cache successful responses.
            if 200 <= captured_status < 300:
                try:
                    async with AsyncSessionLocal() as db:
                        stored = await db.scalar(
                            select(IdempotencyKey).where(IdempotencyKey.id == record.id)
                        )
                        if stored:
                            stored.status_code = captured_status
                            stored.response_json = response_json
                            # Extract content-type from captured headers.
                            content_type = None
                            for hk, hv in captured_headers:
                                if hk == b"content-type":
                                    content_type = hv.decode("latin-1")
                                    break
                            stored.response_content_type = content_type
                            stored.processing = False
                            await db.commit()
                except Exception:
                    logger.warning("Failed to store idempotency response", exc_info=True)
                    await _delete_idempotency_record(record.id)
            else:
                # Non-2xx response — delete the record so the client can retry.
                await _delete_idempotency_record(record.id)

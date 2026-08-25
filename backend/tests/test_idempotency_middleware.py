"""Focused regression tests for idempotency request replay."""
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.middleware.idempotency import _is_exempt, _make_replay_receive


def _scope(method: str, path: str) -> Scope:
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 8000),
        "server": ("testserver", 80),
    }


def test_safe_requests_are_not_idempotency_checked():
    assert _is_exempt(_scope("GET", "/api/v1/quests"))


def test_public_auth_mutations_are_exempt():
    assert _is_exempt(_scope("POST", "/api/v1/auth/login"))
    assert _is_exempt(_scope("POST", "/api/v1/public/stats"))


def test_authenticated_mutations_require_idempotency_tracking():
    assert not _is_exempt(_scope("POST", "/api/v1/quests/123/complete"))
    assert not _is_exempt(_scope("PATCH", "/api/v1/users/me"))


async def test_body_is_replayed_once_then_disconnects():
    receive = _make_replay_receive(b'{"proof":{}}')

    assert await receive() == {
        "type": "http.request",
        "body": b'{"proof":{}}',
        "more_body": False,
    }
    assert await receive() == {"type": "http.disconnect"}


class _PassThroughMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        return await call_next(request)


async def test_replayed_body_is_compatible_with_base_http_middleware():
    """Regression test for production quest-completion response failures."""

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        await JSONResponse({"success": True})(scope, receive, send)

    sent: list[Message] = []

    async def send(message: Message) -> None:
        sent.append(message)

    middleware: ASGIApp = _PassThroughMiddleware(app)
    await middleware(
        _scope("POST", "/api/v1/quests/example/complete"),
        _make_replay_receive(b'{"proof":{}}'),
        send,
    )

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 200

"""Focused tests for idempotency request classification."""
from types import SimpleNamespace

from app.middleware.idempotency import IdempotencyMiddleware


def _request(method: str, path: str):
    return SimpleNamespace(method=method, url=SimpleNamespace(path=path))


def test_safe_requests_are_not_idempotency_checked():
    middleware = IdempotencyMiddleware(lambda scope: None)
    assert middleware._is_exempt(_request("GET", "/api/v1/quests"))


def test_public_auth_mutations_are_exempt():
    middleware = IdempotencyMiddleware(lambda scope: None)
    assert middleware._is_exempt(_request("POST", "/api/v1/auth/login"))
    assert middleware._is_exempt(_request("POST", "/api/v1/public/stats"))


def test_authenticated_mutations_require_idempotency_tracking():
    middleware = IdempotencyMiddleware(lambda scope: None)
    assert not middleware._is_exempt(_request("POST", "/api/v1/quests/123/complete"))
    assert not middleware._is_exempt(_request("PATCH", "/api/v1/users/me"))

"""High-risk token operations distinguish outage from a failed single-use claim."""

from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from httpx import AsyncClient

from app.core import token_blacklist
from app.core.errors import ServiceUnavailableError
from app.core.security import create_token, decode_token


@pytest.fixture
def unavailable_redis(monkeypatch):
    client = AsyncMock()
    client.set.side_effect = ConnectionError("isolated Redis unavailable")
    client.exists.side_effect = ConnectionError("isolated Redis unavailable")
    monkeypatch.setattr("app.core.redis.get_redis", lambda: client)
    return client


async def test_refresh_claim_outage_is_unavailable_not_success(unavailable_redis):
    with pytest.raises(ServiceUnavailableError) as failure:
        await token_blacklist.claim_token_once("synthetic-refresh", 60)
    assert failure.value.status_code == 503


async def test_revocation_outage_cannot_acknowledge_success(unavailable_redis):
    with pytest.raises(ServiceUnavailableError):
        await token_blacklist.blacklist_token("synthetic-access", 60)


@pytest.mark.parametrize("acknowledged", [None, False])
async def test_revocation_requires_write_acknowledgement(monkeypatch, acknowledged):
    client = AsyncMock()
    client.set.return_value = acknowledged
    monkeypatch.setattr("app.core.redis.get_redis", lambda: client)
    with pytest.raises(ServiceUnavailableError):
        await token_blacklist.blacklist_token("synthetic-access", 60)


async def test_ordinary_read_policy_is_not_silently_changed(unavailable_redis):
    assert await token_blacklist.is_token_blacklisted("synthetic-access") is False


async def test_no_jti_refresh_cannot_prove_single_use():
    assert await token_blacklist.claim_token_once(None, 60) is False


async def test_expired_revocation_needs_no_redis(unavailable_redis):
    await token_blacklist.blacklist_token("expired", 0)
    unavailable_redis.set.assert_not_awaited()


async def test_claim_differentiates_already_consumed_from_available(monkeypatch):
    client = AsyncMock()
    client.set.side_effect = [True, None, False]
    monkeypatch.setattr("app.core.redis.get_redis", lambda: client)
    assert await token_blacklist.claim_token_once("once", 60) is True
    assert await token_blacklist.claim_token_once("once", 60) is False
    assert await token_blacklist.claim_token_once("once", 60) is False


async def test_http_refresh_outage_returns_503_without_minting(
    client: AsyncClient, auth_headers, unavailable_redis, monkeypatch
):
    payload = decode_token(auth_headers["Authorization"].split(" ")[1])
    refresh = create_token(payload["sub"], token_type="refresh")
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    mint = Mock()
    monkeypatch.setattr(auth, "create_token", mint)
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert "token" not in response.json()
    mint.assert_not_called()
    unavailable_redis.set.assert_awaited_once()


async def test_http_logout_outage_does_not_report_revoked(
    client: AsyncClient, auth_headers, unavailable_redis, monkeypatch
):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    response = await client.post("/api/v1/auth/logout", headers=auth_headers, json={})
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    unavailable_redis.set.assert_awaited_once()


async def test_http_ordinary_access_remains_fail_open(
    client: AsyncClient, auth_headers, unavailable_redis, monkeypatch
):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    unavailable_redis.exists.assert_awaited_once()


async def test_http_disabled_blacklist_cannot_confirm_logout(client: AsyncClient, auth_headers, monkeypatch):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", False)
    revoke = AsyncMock()
    monkeypatch.setattr(auth, "blacklist_token", revoke)
    response = await client.post("/api/v1/auth/logout", headers=auth_headers, json={})
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    revoke.assert_not_awaited()
    # This is not revocation: the credential still authenticates normally.
    assert (await client.get("/api/v1/users/me", headers=auth_headers)).status_code == 200


def _without_jti(token: str) -> str:
    from app.core.config import get_settings

    settings = get_settings()
    payload = decode_token(token)
    payload.pop("jti")
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def test_http_legacy_access_cannot_confirm_logout(client: AsyncClient, auth_headers, monkeypatch):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    legacy_access = _without_jti(auth_headers["Authorization"].split(" ")[1])
    response = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {legacy_access}"}, json={})
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"


async def test_http_legacy_refresh_cannot_rotate(client: AsyncClient, auth_headers, monkeypatch):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    payload = decode_token(auth_headers["Authorization"].split(" ")[1])
    legacy_refresh = _without_jti(create_token(payload["sub"], token_type="refresh"))
    mint = Mock()
    monkeypatch.setattr(auth, "create_token", mint)
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": legacy_refresh})
    assert response.status_code == 401
    mint.assert_not_called()


async def test_http_legacy_refresh_cannot_confirm_logout(client: AsyncClient, auth_headers, monkeypatch):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    payload = decode_token(auth_headers["Authorization"].split(" ")[1])
    legacy_refresh = _without_jti(create_token(payload["sub"], token_type="refresh"))
    response = await client.post("/api/v1/auth/logout", headers=auth_headers, json={"refresh_token": legacy_refresh})
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"


async def test_http_logout_confirms_both_tokens(client: AsyncClient, auth_headers, monkeypatch):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    payload = decode_token(auth_headers["Authorization"].split(" ")[1])
    refresh = create_token(payload["sub"], token_type="refresh")
    response = await client.post("/api/v1/auth/logout", headers=auth_headers, json={"refresh_token": refresh})
    assert response.status_code == 200
    assert (await client.get("/api/v1/users/me", headers=auth_headers)).status_code == 401
    assert (await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})).status_code == 401


async def test_http_partial_revocation_cannot_confirm_logout(client: AsyncClient, auth_headers, monkeypatch):
    from app.api.v1 import auth

    monkeypatch.setattr(auth.settings, "jwt_blacklist_enabled", True)
    payload = decode_token(auth_headers["Authorization"].split(" ")[1])
    refresh = create_token(payload["sub"], token_type="refresh")
    revoke = AsyncMock(side_effect=[None, ServiceUnavailableError("无法确认撤销")])
    monkeypatch.setattr(auth, "blacklist_token", revoke)
    response = await client.post("/api/v1/auth/logout", headers=auth_headers, json={"refresh_token": refresh})
    assert response.status_code == 503
    assert response.json()["code"] == "SERVICE_UNAVAILABLE"
    assert revoke.await_count == 2

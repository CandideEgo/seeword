"""Tests for the phone-based auth flows: SMS register, phone-login, SMS reset-password,
and change-phone.

Dev-fake SMS mode is forced on (no Aliyun credentials), so the fixed code "1234"
is accepted by verify_code. The production .env has SMS_LOGIN_ENABLED=true with
real Aliyun credentials, which would otherwise make these tests call the live
Aliyun SDK (and fail without network).
"""

import pytest
from httpx import AsyncClient

from tests.conftest import TestSessionLocal

_DEV_FAKE_CODE = "1234"
_TEST_PASSWORD = "Testpass123!"
_TEST_PHONE = "13800138000"
_TEST_PHONE_B = "13800138001"


@pytest.fixture(autouse=True)
def _force_dev_fake_sms(monkeypatch):
    """Force the SMS service into dev-fake mode (accept code '1234')."""
    import app.services.sms_service as sms_svc

    monkeypatch.setattr(sms_svc, "_dev_fake_enabled", lambda: True)


class TestSmsRegister:
    async def test_register_creates_user_and_returns_token(self, client: AsyncClient):
        # Send code with purpose=register
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={
                "phone": _TEST_PHONE,
                "code": _DEV_FAKE_CODE,
                "password": _TEST_PASSWORD,
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "token" in data
        assert data["user"]["phone"] == _TEST_PHONE
        # 免费开放：账号不再带会员字段。
        assert "plan" not in data["user"]
        assert "plan_expires_at" not in data["user"]

    async def test_register_with_name(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={
                "phone": _TEST_PHONE,
                "code": _DEV_FAKE_CODE,
                "password": _TEST_PASSWORD,
                "name": "Phone User",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["user"]["name"] == "Phone User"

    async def test_register_duplicate_phone_returns_409(self, client: AsyncClient, fake_redis):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        # The 60s resend cooldown is a separate guard; clear it so this test
        # exercises the duplicate-phone branch rather than the cooldown.
        await fake_redis.delete(f"sms:cooldown:{_TEST_PHONE}:register")
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        assert resp.status_code == 409
        assert "已注册" in resp.json()["detail"]

    async def test_register_wrong_code_returns_400(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": "0000", "password": _TEST_PASSWORD},
        )
        assert resp.status_code == 400

    async def test_register_weak_password_rejected(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": "weak"},
        )
        assert resp.status_code == 422  # validation error


class TestPhoneLogin:
    async def test_login_with_valid_credentials(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        resp = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": _TEST_PHONE, "password": _TEST_PASSWORD},
        )
        assert resp.status_code == 200
        assert "token" in resp.json()

    async def test_login_wrong_password_returns_401(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        resp = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": _TEST_PHONE, "password": "WrongPass1!"},
        )
        assert resp.status_code == 401

    async def test_login_unregistered_phone_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/phone-login",
            json={"phone": "13900000000", "password": _TEST_PASSWORD},
        )
        assert resp.status_code == 401


class TestSmsLoginAutoCreate:
    """sms/login is the passwordless registration + login entry point."""

    async def test_sms_login_unregistered_creates_phone_only_account(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": "13900000000", "purpose": "auth"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/login",
            json={"phone": "13900000000", "code": _DEV_FAKE_CODE},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["is_new_user"] is True
        assert data["user"]["phone"] == "13900000000"
        # No password was set: password login must not work until one is set.
        assert (
            await client.post(
                "/api/v1/auth/phone-login",
                json={"phone": "13900000000", "password": _TEST_PASSWORD},
            )
        ).status_code == 401

    async def test_sms_login_existing_returns_token_and_is_new_user_false(self, client: AsyncClient, fake_redis):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        # The register above consumed the code; login needs a fresh one (and the
        # resend cooldown must be cleared to obtain it).
        await fake_redis.delete(f"sms:cooldown:{_TEST_PHONE}:register")
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "auth"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/login",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE},
        )
        assert resp.status_code == 200
        assert "token" in resp.json()
        assert resp.json()["is_new_user"] is False

    async def test_first_password_setup_does_not_require_current_or_rotate_session(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "auth"},
        )
        created = await client.post(
            "/api/v1/auth/sms/login",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE},
        )
        token = created.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={"new_password": _TEST_PASSWORD},
        )
        assert resp.status_code == 200, resp.text

        # First setup is not a credential change: the session that set it stays valid.
        assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 200
        assert (
            await client.post(
                "/api/v1/auth/phone-login",
                json={"phone": _TEST_PHONE, "password": _TEST_PASSWORD},
            )
        ).status_code == 200

    async def test_change_password_with_existing_password_still_requires_current(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        created = await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        headers = {"Authorization": f"Bearer {created.json()['token']}"}
        resp = await client.post(
            "/api/v1/auth/change-password",
            headers=headers,
            json={"new_password": "BrandNew123!"},
        )
        assert resp.status_code == 400


class TestSmsResetPassword:
    async def test_reset_password_then_login_with_new(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        new_pw = "BrandNew123!"
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "reset_password"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/reset-password",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "new_password": new_pw},
        )
        assert resp.status_code == 200

        # Old password no longer works
        assert (
            await client.post(
                "/api/v1/auth/phone-login",
                json={"phone": _TEST_PHONE, "password": _TEST_PASSWORD},
            )
        ).status_code == 401
        # New password works
        assert (
            await client.post(
                "/api/v1/auth/phone-login",
                json={"phone": _TEST_PHONE, "password": new_pw},
            )
        ).status_code == 200

    async def test_reset_password_unregistered_returns_same_message(self, client: AsyncClient):
        """Must not reveal whether the phone is registered (anti-enumeration)."""
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": "13900000000", "purpose": "reset_password"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/reset-password",
            json={"phone": "13900000000", "code": _DEV_FAKE_CODE, "new_password": "AnyNew123!"},
        )
        assert resp.status_code == 200
        assert "已注册" in resp.json()["message"]

    async def test_reset_password_wrong_code_returns_400(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "reset_password"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/reset-password",
            json={"phone": _TEST_PHONE, "code": "0000", "new_password": "AnyNew123!"},
        )
        assert resp.status_code == 400

    async def test_reset_password_invalidates_old_session(self, client: AsyncClient):
        """Resetting must invalidate tokens issued before the reset."""
        import uuid
        from datetime import UTC, datetime, timedelta

        import jwt

        from app.core.config import get_settings

        # Register, then mint an "old" access token (iat 60s ago).
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        user_id = resp.json()["user"]["id"]

        settings = get_settings()
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=settings.jwt_expire_minutes)
        old_token = jwt.encode(
            {
                "sub": user_id,
                "exp": expire,
                "iat": now - timedelta(seconds=60),
                "type": "access",
                "jti": uuid.uuid4().hex,
            },
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
        old_headers = {"Authorization": f"Bearer {old_token}"}

        # Move password_changed_at into the past so the old token is initially valid.
        async with TestSessionLocal() as db:
            from app.models.user import User as UserModel

            db_user = await db.get(UserModel, user_id)
            db_user.password_changed_at = datetime.now(UTC) - timedelta(minutes=10)
            await db.commit()

        assert (await client.get("/api/v1/users/me", headers=old_headers)).status_code == 200

        # Reset the password (sets password_changed_at = now).
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE, "purpose": "reset_password"},
        )
        await client.post(
            "/api/v1/auth/sms/reset-password",
            json={"phone": _TEST_PHONE, "code": _DEV_FAKE_CODE, "new_password": "FreshPass123!"},
        )

        # Old token must now be rejected.
        assert (await client.get("/api/v1/users/me", headers=old_headers)).status_code == 401


class TestChangePhone:
    """Tests for the /auth/sms/change-phone endpoint."""

    async def _register_and_get_headers(self, client: AsyncClient, phone: str = _TEST_PHONE):
        """Helper: register a user and return auth headers."""
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": phone, "purpose": "register"},
        )
        resp = await client.post(
            "/api/v1/auth/sms/register",
            json={"phone": phone, "code": _DEV_FAKE_CODE, "password": _TEST_PASSWORD},
        )
        token = resp.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_change_phone_success(self, client: AsyncClient):
        headers = await self._register_and_get_headers(client, phone=_TEST_PHONE)

        # Send change_phone code to the NEW phone
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE_B, "purpose": "change_phone"},
        )

        resp = await client.post(
            "/api/v1/auth/sms/change-phone",
            json={
                "new_phone": _TEST_PHONE_B,
                "code": _DEV_FAKE_CODE,
                "password": _TEST_PASSWORD,
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["phone"] == _TEST_PHONE_B

    async def test_change_phone_wrong_password(self, client: AsyncClient):
        headers = await self._register_and_get_headers(client, phone=_TEST_PHONE)

        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE_B, "purpose": "change_phone"},
        )

        resp = await client.post(
            "/api/v1/auth/sms/change-phone",
            json={
                "new_phone": _TEST_PHONE_B,
                "code": _DEV_FAKE_CODE,
                "password": "WrongPass1!",
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert "密码错误" in resp.json()["detail"]

    async def test_change_phone_wrong_code(self, client: AsyncClient):
        headers = await self._register_and_get_headers(client, phone=_TEST_PHONE)

        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE_B, "purpose": "change_phone"},
        )

        resp = await client.post(
            "/api/v1/auth/sms/change-phone",
            json={
                "new_phone": _TEST_PHONE_B,
                "code": "0000",
                "password": _TEST_PASSWORD,
            },
            headers=headers,
        )
        assert resp.status_code == 400
        assert "验证码" in resp.json()["detail"]

    async def test_change_phone_phone_already_registered(self, client: AsyncClient):
        # Register two users: A and B
        headers_a = await self._register_and_get_headers(client, phone=_TEST_PHONE)
        await self._register_and_get_headers(client, phone=_TEST_PHONE_B)

        # Try to change A's phone to B's phone (already registered)
        await client.post(
            "/api/v1/auth/sms/send-code",
            json={"phone": _TEST_PHONE_B, "purpose": "change_phone"},
        )

        resp = await client.post(
            "/api/v1/auth/sms/change-phone",
            json={
                "new_phone": _TEST_PHONE_B,
                "code": _DEV_FAKE_CODE,
                "password": _TEST_PASSWORD,
            },
            headers=headers_a,
        )
        assert resp.status_code == 409
        assert "已被注册" in resp.json()["detail"]

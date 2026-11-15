"""运营者首建/普通账号：输入契约、幂等和密码重置会话失效。"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import RoleType, User
from scripts.create_admin import _create_or_promote, validate_inputs


@pytest.mark.parametrize("phone", ["", "123", "+8613900000000", "11900000000"])
def test_invalid_phone(phone):
    with pytest.raises(ValueError):
        validate_inputs(phone, "Valid123!", False)


@pytest.mark.parametrize("password", ["", "Short1", "alllower123", "A1" + "中" * 24, "A1" + "a" * 71])
def test_invalid_password(password):
    with pytest.raises(ValueError):
        validate_inputs("13900000000", password, False)


def test_password_utf8_boundary():
    validate_inputs("13900000000", "Aa1" + "中" * 23, False)
    with pytest.raises(ValueError):
        validate_inputs("13900000000", None, True)


async def test_create_regular_user_then_promote_and_reset(db_session):
    phone = "13900000000"
    await _create_or_promote(phone, "Valid123!", False, role=RoleType.user)
    user = await db_session.scalar(select(User).where(User.phone == phone))
    assert user.role == RoleType.user
    assert verify_password("Valid123!", user.hashed_password)
    assert not user.onboarding_completed
    old_hash = user.hashed_password
    await _create_or_promote(phone, "Other123!", False, role=RoleType.user)
    await db_session.refresh(user)
    assert user.hashed_password == old_hash
    user.password_changed_at = datetime(2020, 1, 1, tzinfo=UTC)
    await db_session.commit()
    await _create_or_promote(phone, "Reset123!", True)
    await db_session.refresh(user)
    assert user.role == RoleType.admin
    assert verify_password("Reset123!", user.hashed_password)
    assert user.password_changed_at.year > 2020
    await _create_or_promote(phone, None, False, role=RoleType.user)
    await db_session.refresh(user)
    assert user.role == RoleType.admin


async def test_creation_refuses_development_database_fallback(monkeypatch):
    from unittest.mock import Mock

    from scripts import create_admin

    factory = Mock()
    monkeypatch.setattr(create_admin, "get_settings", lambda: Mock(model_fields_set=set()))
    monkeypatch.setattr(create_admin, "get_async_session_maker", factory)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        await _create_or_promote("13900000000", "Valid123!", False)
    factory.assert_not_called()


async def test_new_account_needs_password(db_session):
    with pytest.raises(ValueError, match="密码"):
        await _create_or_promote("13900000000", None, False)
    assert await db_session.scalar(select(User).where(User.phone == "13900000000")) is None


async def test_banned_or_deleting_account_not_revived(db_session):
    user = User(phone="13900000000", role=RoleType.user, is_banned=True)
    db_session.add(user)
    await db_session.commit()
    with pytest.raises(ValueError, match="封禁"):
        await _create_or_promote(user.phone, "Reset123!", True)
    user.is_banned = False
    user.deletion_requested_at = datetime.now(UTC)
    await db_session.commit()
    with pytest.raises(ValueError, match="注销"):
        await _create_or_promote(user.phone, "Reset123!", True)
    await db_session.refresh(user)
    assert user.role == RoleType.user
    assert user.hashed_password is None

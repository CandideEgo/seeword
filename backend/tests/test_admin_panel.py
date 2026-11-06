"""Tests for the admin-panel alignment endpoints (prototypes 24-32).

Covers: settings singleton (GET/PUT), admin account list, user list expired
filter / learned_words, and stats funnel/topic extensions.
"""

from httpx import AsyncClient


class TestAdminSettings:
    async def test_settings_requires_admin(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/admin/settings", headers=auth_headers)
        assert resp.status_code == 403

    async def test_settings_defaults(self, client: AsyncClient, admin_headers: dict):
        resp = await client.get("/api/v1/admin/settings", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["site_name"] == "SeeWord"
        assert data["registration_enabled"] is True
        assert data["quality_block_enabled"] is True
        assert data["quality_block_threshold"] == 0.6
        assert data["quality_warn_threshold"] == 0.8
        assert data["translate_timeout_sec"] == 1800
        assert data["download_timeout_sec"] == 3600

    async def test_settings_partial_update(self, client: AsyncClient, admin_headers: dict):
        resp = await client.put(
            "/api/v1/admin/settings",
            headers=admin_headers,
            json={"site_name": "SeeWord Beta", "quality_warn_threshold": 0.85},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["site_name"] == "SeeWord Beta"
        assert data["quality_warn_threshold"] == 0.85

        # persisted across requests
        again = await client.get("/api/v1/admin/settings", headers=admin_headers)
        assert again.json()["site_name"] == "SeeWord Beta"

    async def test_settings_threshold_validation(self, client: AsyncClient, admin_headers: dict):
        resp = await client.put(
            "/api/v1/admin/settings",
            headers=admin_headers,
            json={"quality_warn_threshold": 0.3, "quality_block_threshold": 0.6},
        )
        assert resp.status_code == 400


class TestAdminAccounts:
    async def test_list_admin_accounts(self, client: AsyncClient, admin_headers: dict):
        resp = await client.get("/api/v1/admin/admins", headers=admin_headers)
        assert resp.status_code == 200
        accounts = resp.json()
        assert isinstance(accounts, list)
        assert len(accounts) >= 1
        assert accounts[0]["name"] == "Admin"
        assert accounts[0]["phone"] == "13900139000"


class TestAdminUsersEnhanced:
    async def test_learned_words_present(self, client: AsyncClient, admin_headers: dict):
        resp = await client.get("/api/v1/admin/users", headers=admin_headers)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert "learned_words" in item


class TestAdminStatsEnhanced:
    async def test_stats_new_fields(self, client: AsyncClient, admin_headers: dict):
        resp = await client.get("/api/v1/admin/stats", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["videos_by_topic"], list)
        funnel = data["funnel"]
        assert {"registered", "watched", "vocab_saved"} <= set(funnel.keys())
        assert funnel["registered"] >= 1


class TestAdminUserFilterValidation:
    """ADM-11: invalid enum filters are 422, keyword wildcards are escaped."""

    async def test_invalid_role_is_422(self, client: AsyncClient, admin_headers: dict):
        resp = await client.get("/api/v1/admin/users", params={"role": "bogus"}, headers=admin_headers)
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"

    async def test_keyword_wildcards_are_escaped(self, client: AsyncClient, admin_headers: dict):
        # "%" used to match the whole table; now it must be a literal character.
        resp = await client.get("/api/v1/admin/users", params={"keyword": "%"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        resp = await client.get("/api/v1/admin/users", params={"keyword": "_"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_keyword_length_limit(self, client: AsyncClient, admin_headers: dict):
        resp = await client.get("/api/v1/admin/users", params={"keyword": "x" * 101}, headers=admin_headers)
        assert resp.status_code == 422


class TestAdminUserListPagination:
    """ADM-10: ordering has an id tiebreaker so OFFSET pagination is stable."""

    async def test_equal_timestamps_do_not_duplicate_across_pages(
        self, client: AsyncClient, db_session, admin_headers: dict
    ):
        from datetime import datetime

        from app.models.user import User

        ts = datetime(2026, 1, 1, 12, 0, 0)
        for i in range(4):
            db_session.add(User(phone=f"1370013700{i}", name=f"Same {i}", created_at=ts))
        await db_session.commit()

        first = await client.get("/api/v1/admin/users", params={"page": 1, "page_size": 2}, headers=admin_headers)
        second = await client.get("/api/v1/admin/users", params={"page": 2, "page_size": 2}, headers=admin_headers)
        assert first.status_code == second.status_code == 200
        ids1 = [item["id"] for item in first.json()["items"]]
        ids2 = [item["id"] for item in second.json()["items"]]
        assert len(ids1) == len(ids2) == 2
        assert not set(ids1) & set(ids2)
        assert first.json()["total"] == 5  # 4 + the admin fixture user


class TestLastAdminProtection:
    """ADM-09: mutations cannot leave zero usable admins.

    The API-level self guard makes the last-admin case unreachable for a single
    request (the actor is itself an admin), so the guarantee is exercised at
    the service layer — that is exactly the path the concurrent mutual-ban
    scenario takes for the transaction that loses the race.
    """

    async def _make_admin(self, db, phone: str) -> "object":
        from app.models.user import RoleType, User

        user = User(
            phone=phone,
            name="Second Admin",
            role=RoleType.admin,
            is_banned=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def test_cannot_ban_last_usable_admin(self, db_session):
        from app.core.errors import ConflictError
        from app.models.user import RoleType, User
        from app.services import admin_service

        only_admin = User(phone="13600136009", name="Only Admin", role=RoleType.admin)
        db_session.add(only_admin)
        await db_session.commit()
        await db_session.refresh(only_admin)

        # Actor is another (hypothetical) admin: the API's self-guard is not
        # what we are testing here — the last-admin rule is.
        try:
            await admin_service.ban_user(db_session, only_admin.id, True, admin_user_id="someone-else")
        except ConflictError as exc:
            assert exc.status_code == 409
        else:  # pragma: no cover - the guard must fire
            raise AssertionError("banning the last usable admin must be rejected")

        await db_session.refresh(only_admin)
        assert only_admin.is_banned is False

    async def test_cannot_demote_last_usable_admin(self, db_session):
        from app.core.errors import ConflictError
        from app.models.user import RoleType, User
        from app.services import admin_service

        only_admin = User(phone="13600136010", name="Only Admin", role=RoleType.admin)
        db_session.add(only_admin)
        await db_session.commit()
        await db_session.refresh(only_admin)

        try:
            await admin_service.change_user_role(db_session, only_admin.id, "user", admin_user_id="someone-else")
        except ConflictError as exc:
            assert exc.status_code == 409
        else:  # pragma: no cover
            raise AssertionError("demoting the last usable admin must be rejected")

        await db_session.refresh(only_admin)
        assert only_admin.role.value == "admin"

    async def test_can_ban_admin_when_another_remains(self, db_session):
        from app.models.user import RoleType, User
        from app.services import admin_service

        survivor = User(phone="13600136011", name="Survivor", role=RoleType.admin)
        target = User(phone="13600136012", name="Target", role=RoleType.admin)
        db_session.add_all([survivor, target])
        await db_session.commit()
        await db_session.refresh(survivor)
        await db_session.refresh(target)

        banned = await admin_service.ban_user(db_session, target.id, True, admin_user_id=survivor.id)
        assert banned.is_banned is True

    async def test_banned_admin_does_not_count_as_usable(self, db_session):
        """A banned admin is not a fallback — it cannot take over the panel."""
        from app.core.errors import ConflictError
        from app.models.user import RoleType, User
        from app.services import admin_service

        survivor = User(phone="13600136013", name="Survivor", role=RoleType.admin)
        banned_admin = User(phone="13600136014", name="Banned Admin", role=RoleType.admin, is_banned=True)
        db_session.add_all([survivor, banned_admin])
        await db_session.commit()
        await db_session.refresh(survivor)

        try:
            await admin_service.ban_user(db_session, survivor.id, True, admin_user_id="someone-else")
        except ConflictError:
            pass
        else:  # pragma: no cover
            raise AssertionError("a banned admin must not satisfy the last-admin rule")

    async def test_api_self_ban_and_self_demote_still_guarded(self, client: AsyncClient, admin_headers: dict):
        users = await client.get("/api/v1/admin/users", params={"keyword": "13900139000"}, headers=admin_headers)
        admin_id = users.json()["items"][0]["id"]
        ban = await client.patch(f"/api/v1/admin/users/{admin_id}/ban", json={"is_banned": True}, headers=admin_headers)
        assert ban.status_code == 400
        role = await client.patch(f"/api/v1/admin/users/{admin_id}/role", json={"role": "user"}, headers=admin_headers)
        assert role.status_code == 400


class TestAdminSettingsConcurrencySafety:
    """ADM-14: settings init is race-safe and validation happens pre-mutation."""

    async def test_invalid_threshold_does_not_mutate_settings(self, db_session):
        import pytest

        from app.core.errors import BadRequestError
        from app.services import admin_service

        settings = await admin_service.get_admin_settings(db_session)
        original_name = settings.site_name

        with pytest.raises(BadRequestError):
            await admin_service.update_admin_settings(
                db_session, {"quality_warn_threshold": 0.1, "site_name": "Mutated"}
            )

        # Same session → same identity-map object: a pre-validation mutation
        # would be visible here even though nothing was committed.
        current = await admin_service.get_admin_settings(db_session)
        assert current.site_name == original_name
        assert float(current.quality_warn_threshold) == 0.8

    async def test_settings_row_is_created_once(self, db_session):
        """Repeated first-reads return one row; a second insert must not 500."""
        from sqlalchemy import func, select

        from app.models.admin_setting import AdminSetting
        from app.services import admin_service

        first = await admin_service.get_admin_settings(db_session)
        second = await admin_service.get_admin_settings(db_session)
        assert first.id == second.id
        count = (await db_session.execute(select(func.count(AdminSetting.id)))).scalar_one()
        assert count == 1

"""P1-7: 30-day cancellable deletion + async data export.

Runs on the in-memory SQLite test DB with the shared async loop helper, so the
task bodies execute against the same test data the request bodies wrote. The
media root is redirected to a tmp dir so no real exports land in the repo.
"""

import zipfile
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.models.behavior import BehaviorEvent
from app.models.data_export import DataExportTask
from app.models.learning import Vocabulary
from app.models.user import User
from app.tasks.account_tasks import _purge_due, build_user_export
from tests.conftest import TestSessionLocal


@pytest.fixture
def media_tmp(tmp_path, monkeypatch):
    """Redirect the media root at a per-test tmp dir (returns the Path)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "local_media_path", str(tmp_path))
    return tmp_path


async def _me(client: AsyncClient, auth_headers: dict) -> dict:
    return (await client.get("/api/v1/users/me", headers=auth_headers)).json()


# ── Deletion request / cancel / status ──────────────────────────────


async def test_request_deletion_requires_confirm(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/users/me/deletion", json={"confirm": False}, headers=auth_headers)
    assert resp.status_code == 400


async def test_request_deletion_schedules_30_days_and_is_idempotent(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/users/me/deletion",
        json={"confirm": True, "reason": "换个账号"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scheduled"] is True
    assert body["days_remaining"] == 30
    assert body["reason"] == "换个账号"
    scheduled_at = datetime.fromisoformat(body["scheduled_at"])

    # A second request keeps the original schedule (no silent extension).
    again = (await client.post("/api/v1/users/me/deletion", json={"confirm": True}, headers=auth_headers)).json()
    assert datetime.fromisoformat(again["scheduled_at"]) == scheduled_at

    # Status endpoint mirrors the schedule.
    status = (await client.get("/api/v1/users/me/deletion", headers=auth_headers)).json()
    assert status["scheduled"] is True

    # The user can still log in / use the API during the window.
    assert (await client.get("/api/v1/users/me", headers=auth_headers)).status_code == 200


async def test_cancel_deletion_clears_fields(client: AsyncClient, auth_headers: dict):
    await client.post("/api/v1/users/me/deletion", json={"confirm": True}, headers=auth_headers)

    resp = await client.delete("/api/v1/users/me/deletion", headers=auth_headers)
    assert resp.status_code == 200

    status = (await client.get("/api/v1/users/me/deletion", headers=auth_headers)).json()
    assert status["scheduled"] is False
    assert status["scheduled_at"] is None


# ── Purge ───────────────────────────────────────────────────────────


async def test_purge_releases_phone_and_anonymizes_behavior(client: AsyncClient, auth_headers: dict, media_tmp):
    me = await _me(client, auth_headers)
    user_id = me["id"]
    phone = me["phone"]

    async with TestSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        user.deletion_requested_at = datetime.now(UTC) - timedelta(days=31)
        user.deletion_scheduled_at = datetime.now(UTC) - timedelta(days=1)
        db.add(BehaviorEvent(user_id=user_id, event_type="watch_time", event_payload={"s": 3}))
        db.add(Vocabulary(user_id=user_id, word="apple"))
        await db.commit()

    purged = await _purge_due(now=datetime.now(UTC))
    assert purged == 1

    async with TestSessionLocal() as db:
        assert (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none() is None
        assert (await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id))).scalars().all() == []
        # Behavior events survive, anonymized.
        events = (await db.execute(select(BehaviorEvent))).scalars().all()
        assert len(events) == 1
        assert events[0].user_id is None

    # Phone is released only after deletion — a fresh account can take it.
    async with TestSessionLocal() as db:
        db.add(User(phone=phone, hashed_password=None, name="Fresh"))
        await db.commit()


async def test_purge_keeps_not_yet_due_accounts(client: AsyncClient, auth_headers: dict, media_tmp):
    me = await _me(client, auth_headers)
    async with TestSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == me["id"]))).scalar_one()
        user.deletion_scheduled_at = datetime.now(UTC) + timedelta(days=5)
        await db.commit()

    assert await _purge_due(now=datetime.now(UTC)) == 0

    async with TestSessionLocal() as db:
        assert (await db.execute(select(User).where(User.id == me["id"]))).scalar_one_or_none() is not None


# ── Export ──────────────────────────────────────────────────────────


async def test_export_builds_zip_with_media_and_serves_once(client: AsyncClient, auth_headers: dict, media_tmp):
    me = await _me(client, auth_headers)
    user_id = me["id"]

    # Seed data + on-disk media (avatar).
    (media_tmp / "avatars").mkdir(parents=True, exist_ok=True)
    (media_tmp / "avatars" / "face.png").write_bytes(b"avatar-bytes")

    async with TestSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        user.avatar_url = "/media/avatars/face.png"
        db.add(Vocabulary(user_id=user_id, word="apple", translation="n. 苹果"))
        await db.commit()

    created = await client.get("/api/v1/users/me/export", headers=auth_headers)
    assert created.status_code == 200
    task_id = created.json()["task_id"]
    assert created.json()["status"] == "pending"

    # Celery dispatch is stubbed in tests — run the task body directly.
    result = build_user_export(task_id)
    assert result["status"] == "ready"

    async with TestSessionLocal() as db:
        task = (await db.execute(select(DataExportTask).where(DataExportTask.id == task_id))).scalar_one()
        zip_rel = task.file_path
        assert task.status == "ready"
        assert zip_rel is not None

    # The ZIP carries structured data plus the media originals.
    with zipfile.ZipFile(media_tmp / zip_rel) as zf:
        names = set(zf.namelist())
        assert "vocabulary.csv" in names
        assert "vocabulary.json" in names
        assert "learning_records.json" in names
        assert "preferences.json" in names
        assert "behavior_events.csv" in names
        assert any(n.startswith("media/avatar/") for n in names)
        # Retired features have no data tables; historical shadowing audio
        # is still account-owned media (privacy page promises it in export).
        assert "shadowing.csv" not in names

    status = (await client.get(f"/api/v1/users/me/export/{task_id}", headers=auth_headers)).json()
    assert status["status"] == "ready"
    assert status["download_url"]

    download = await client.get(status["download_url"], headers=auth_headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"

    # Single-use: the same URL is now gone.
    second = await client.get(status["download_url"], headers=auth_headers)
    assert second.status_code == 410


async def test_export_status_of_other_users_task_returns_404(client: AsyncClient, auth_headers: dict, media_tmp):
    from app.core.security import create_token, hash_password
    from app.models.user import RoleType

    async with TestSessionLocal() as db:
        other = User(
            phone="13800137777",
            hashed_password=hash_password("Otherpass1!"),
            name="Other",
            role=RoleType.user,
        )
        db.add(other)
        await db.commit()
        await db.refresh(other)
        other_headers = {"Authorization": f"Bearer {create_token(other.id)}"}

    me = await _me(client, auth_headers)
    async with TestSessionLocal() as db:
        task = DataExportTask(user_id=me["id"], status="ready")
        db.add(task)
        await db.commit()
        task_id = task.id

    resp = await client.get(f"/api/v1/users/me/export/{task_id}", headers=other_headers)
    assert resp.status_code == 404

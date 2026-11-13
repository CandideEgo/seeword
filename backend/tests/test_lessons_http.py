"""HTTP surface of the SLCS lesson pilot: gates, authorization and import limits."""

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.lesson import LessonRevision
from app.models.user import RoleType, User
from tests.conftest import TestSessionLocal

PACK = Path(__file__).resolve().parents[2] / "docs" / "slcs" / "examples" / "welcome-to-wikisource.json"


@pytest.fixture
def pack_text() -> str:
    return PACK.read_text(encoding="utf-8")


def enable_pilot(monkeypatch, *, lessons=True, tutor=False, vocabulary=False):
    settings = get_settings()
    monkeypatch.setattr(settings, "slcs_lessons_enabled", lessons)
    monkeypatch.setattr(settings, "slcs_tutor_enabled", tutor)
    monkeypatch.setattr(settings, "slcs_vocabulary_enabled", vocabulary)
    return settings


async def test_pilot_gates_every_lesson_route_when_disabled(client, auth_headers, monkeypatch):
    enable_pilot(monkeypatch, lessons=False)
    assert (await client.get("/api/v1/lessons/_status", headers=auth_headers)).json() == {"enabled": False}
    for path in ("/api/v1/lessons", "/api/v1/lessons/welcome-to-wikisource", "/api/v1/lessons/_history"):
        response = await client.get(path, headers=auth_headers)
        assert response.status_code == 503, path
        assert response.json()["code"] == "SERVICE_UNAVAILABLE"


async def test_admin_routes_require_an_admin(client, auth_headers, monkeypatch):
    enable_pilot(monkeypatch)
    disabled = await client.get("/api/v1/admin/lessons", headers=auth_headers)
    assert disabled.status_code == 403


async def test_import_and_publish_require_an_admin(client, auth_headers, monkeypatch, pack_text):
    enable_pilot(monkeypatch)
    payload = {"operation_id": "http-import-1", "pack_json": pack_text}
    response = await client.post("/api/v1/admin/lessons/import", json=payload, headers=auth_headers)
    assert response.status_code == 403


async def test_import_is_idempotent_over_http(client, admin_headers, monkeypatch, pack_text):
    enable_pilot(monkeypatch)
    payload = {"operation_id": "http-import-1", "pack_json": pack_text}
    first = await client.post("/api/v1/admin/lessons/import", json=payload, headers=admin_headers)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "candidate"
    assert body["fingerprint_version"] == "slcs-pack-v1"

    replay = await client.post("/api/v1/admin/lessons/import", json=payload, headers=admin_headers)
    assert replay.status_code == 200
    assert replay.json()["revision_id"] == body["revision_id"]
    assert replay.json()["replayed"] is True

    async with TestSessionLocal() as db:
        revisions = list(
            await db.scalars(select(LessonRevision).where(LessonRevision.lesson_id == "welcome-to-wikisource"))
        )
        assert len(revisions) == 1


async def test_import_reports_field_paths_for_an_invalid_pack(client, admin_headers, monkeypatch, pack_text):
    enable_pilot(monkeypatch)
    document = json.loads(pack_text)
    document["schema_version"] = "0.2.0"
    response = await client.post(
        "/api/v1/admin/lessons/import",
        json={"operation_id": "http-invalid-1", "pack_json": json.dumps(document)},
        headers=admin_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["detail"][0]["path"] == "/schema_version"


async def test_import_refuses_an_oversized_body_before_parsing(client, admin_headers, monkeypatch):
    enable_pilot(monkeypatch)
    oversized = "x" * (8 * 1024 * 1024 + 1)
    response = await client.post(
        "/api/v1/admin/lessons/import",
        content=oversized,
        headers={**admin_headers, "content-type": "application/json"},
    )
    assert response.status_code == 413


async def test_lists_only_published_and_reviewed_revisions(client, admin_headers, auth_headers, monkeypatch, pack_text):
    settings = enable_pilot(monkeypatch)
    monkeypatch.setattr(settings, "slcs_lesson_receipt_issuer", "")
    monkeypatch.setattr(settings, "slcs_lesson_receipt_public_keys", {})
    response = await client.post(
        "/api/v1/admin/lessons/import",
        json={"operation_id": "http-import-list", "pack_json": pack_text},
        headers=admin_headers,
    )
    assert response.status_code == 200
    revision_id = response.json()["revision_id"]

    # A candidate is invisible to learners and never listed publicly.
    assert (await client.get("/api/v1/lessons", headers=auth_headers)).json() == {"lessons": []}
    hidden = await client.get("/api/v1/lessons/welcome-to-wikisource", headers=auth_headers)
    assert hidden.status_code == 404

    review = await client.post(
        f"/api/v1/admin/lessons/welcome-to-wikisource/revisions/{revision_id}/review",
        json={
            "operation_id": "http-review-1",
            "source_commit": "a" * 40,
            "uses": {
                "site_display": {"approved": True, "evidence": "synthetic HTTP test"},
                "model_processing": {"approved": False, "evidence": "not requested"},
                "external_redistribution": {"approved": False, "evidence": "not requested"},
            },
        },
        headers=admin_headers,
    )
    assert review.status_code == 200, review.text
    assert review.json()["review"]["uses"]["site_display"]["approved"] is True

    # Publishing is refused until a receipt signer is configured, and says so.
    publish = await client.post(
        f"/api/v1/admin/lessons/welcome-to-wikisource/revisions/{revision_id}/publish",
        json={"operation_id": "http-publish-1", "expected_current_revision_id": None, "receipt": "token"},
        headers=admin_headers,
    )
    assert publish.status_code == 503


async def test_lesson_route_requires_a_login(client, monkeypatch):
    enable_pilot(monkeypatch)
    async with TestSessionLocal() as db:
        db.add(User(role=RoleType.user, phone="13800001299", name="Anonymous target"))
        await db.commit()
    response = await client.get("/api/v1/lessons")
    assert response.status_code == 401

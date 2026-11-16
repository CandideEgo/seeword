"""HTTP surface of the SLCS lesson pilot: gates, authorization and import limits."""

import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import func, select

from app.core.config import get_settings
from app.models.lesson import Lesson, LessonOperation, LessonRevision
from app.models.user import RoleType, User
from scripts import sign_lesson_receipt as signer
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


async def test_admin_diff_is_gated_private_scoped_and_read_only(
    client, admin_headers, auth_headers, monkeypatch, pack_text
):
    enable_pilot(monkeypatch)
    document = json.loads(pack_text)
    lesson_id = document["lesson_id"]

    async def imported(operation, pack):
        response = await client.post(
            "/api/v1/admin/lessons/import",
            json={"operation_id": operation, "pack_json": json.dumps(pack)},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.text
        return response.json()["revision_id"]

    baseline = await imported("diff-baseline", document)
    document["segments"][0]["translation"] += "（合成纠错测试）"
    revision = await imported("diff-candidate", document)
    url = f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision}/diff"
    query = {"baseline_revision_id": baseline}
    assert (await client.get(url, params=query)).status_code == 401
    assert (await client.get(url, params=query, headers=auth_headers)).status_code == 403
    response = await client.get(url, params=query, headers=admin_headers)
    assert response.status_code == 200, response.text
    assert response.headers["Cache-Control"] == "private, no-store"
    body = response.json()
    assert body["revision_id"] == revision and body["baseline_revision_id"] == baseline
    assert body["impacts"] == ["translation"]
    assert body["changes"][0]["path"] == f"/segments/{document['segments'][0]['id']}/translation"
    assert body["changes"][0]["after"] == document["segments"][0]["translation"]
    same = await client.get(url, params={"baseline_revision_id": revision}, headers=admin_headers)
    assert same.json()["changes"] == []
    for params in ({}, {"baseline_revision_id": ""}, {"baseline_revision_id": "x" * 37}):
        assert (await client.get(url, params=params, headers=admin_headers)).status_code == 422
    document["lesson_id"] = "another-diff-lesson"
    foreign = await imported("diff-foreign", document)
    assert (await client.get(url, params={"baseline_revision_id": foreign}, headers=admin_headers)).status_code == 404
    assert (await client.get(url, params={"baseline_revision_id": "missing"}, headers=admin_headers)).status_code == 404
    async with TestSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(LessonOperation)) == 3
    enable_pilot(monkeypatch, lessons=False)
    assert (await client.get(url, params=query, headers=admin_headers)).status_code == 503


async def test_http_restore_requires_new_review_and_does_not_consume_failed_operations(
    client, admin_headers, monkeypatch, pack_text
):
    settings = enable_pilot(monkeypatch)
    key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(settings, "slcs_lesson_receipt_issuer", "test-http-signer")
    monkeypatch.setattr(settings, "slcs_lesson_receipt_public_keys", {"test-http": signer.public_pem(key)})
    imported = await client.post(
        "/api/v1/admin/lessons/import",
        json={"operation_id": "restore-import", "pack_json": pack_text},
        headers=admin_headers,
    )
    assert imported.status_code == 200, imported.text
    detail = imported.json()
    lesson_id, revision_id = detail["lesson_id"], detail["revision_id"]
    url = f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}"
    review_body = {
        "source_commit": "a" * 40,
        "verification_method": "synthetic HTTP fixture, not listening evidence",
        "limitations": "test only",
        "human_minutes": None,
        "uses": {
            name: {"approved": name == "site_display", "evidence": "synthetic test only"}
            for name in ("site_display", "model_processing", "external_redistribution")
        },
    }

    async def action(name, operation_id, **body):
        return await client.post(url + "/" + name, json={"operation_id": operation_id, **body}, headers=admin_headers)

    def sign(reviewed):
        receipt = signer.build_claims({**reviewed, "id": revision_id})
        return signer.sign_receipt(receipt, key, issuer="test-http-signer", kid="test-http", ttl=600)

    review = await action("review", "restore-review", **review_body)
    assert review.status_code == 200, review.text
    assert review.json()["review"]["human_minutes"] is None
    unused_old = sign(review.json())
    published = await action(
        "publish", "restore-publish", expected_current_revision_id=None, receipt=sign(review.json())
    )
    assert published.status_code == 200, published.text
    withdrawn = await action("withdraw", "restore-withdraw", reason="synthetic test withdrawal")
    assert withdrawn.status_code == 200 and withdrawn.json()["requires_review"]
    refused = await action("publish", "restore-attempt", expected_current_revision_id=None, receipt=unused_old)
    assert refused.status_code == 422, refused.text
    async with TestSessionLocal() as db:
        assert (await db.get(Lesson, lesson_id)).current_revision_id is None
        assert await db.scalar(select(LessonOperation).where(LessonOperation.operation_id == "restore-attempt")) is None
    replay = await action("review", "restore-review", **review_body)
    assert replay.json()["replayed"] and replay.json()["requires_review"]
    renewed = await action("review", "restore-review-new", **review_body)
    assert renewed.status_code == 200 and not renewed.json()["requires_review"]
    assert renewed.json()["pack"] == detail["pack"]
    assert renewed.json()["fingerprint"] == detail["fingerprint"]
    # A hash mismatch still leaves the same operation ID reusable with the right receipt.
    refused = await action("publish", "restore-attempt", expected_current_revision_id=None, receipt=unused_old)
    assert refused.status_code == 422
    restored = await action(
        "publish", "restore-attempt", expected_current_revision_id=None, receipt=sign(renewed.json())
    )
    assert restored.status_code == 200 and restored.json()["status"] == "published", restored.text

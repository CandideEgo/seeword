"""SLCS review, signed publication, revision access, and isolated learning facts."""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base
from app.core.errors import AppError
from app.models.learning_plan import LearningEvent
from app.models.lesson import Lesson, LessonActivity, LessonProgress, LessonRevision
from app.models.user import RoleType, User
from app.schemas.lesson import PublishLesson, RecordLessonActivity, ReviewLesson, SaveLessonProgress, WithdrawLesson
from app.services import lesson_progress, lessons
from app.services.account_data import _gather_lesson_data
from app.services.lesson_receipts import AUDIENCE, TOKEN_TYPE
from app.services.study_time_service import watch_seconds_by_local_day

REFERENCE = Path(__file__).resolve().parents[2] / "docs" / "slcs" / "examples" / "welcome-to-wikisource.json"


@pytest_asyncio.fixture(params=["sqlite", pytest.param("postgresql", marks=pytest.mark.integration)])
async def lesson_db(request):
    """A throwaway database for the publication workflow.

    The Postgres leg reuses the shared test engine (``PG_TEST_URL``, whose schema
    the autouse fixture already creates) instead of reading a second URL: two
    variables that drifted apart would create the schema on one database and
    assert against another. A separate engine is only made for SQLite.
    """
    if request.param == "postgresql":
        from tests.conftest import _pg_engine_or_skip

        engine = await _pg_engine_or_skip()
        yield async_sessionmaker(engine, expire_on_commit=False), True
        return
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        yield async_sessionmaker(engine, expire_on_commit=False), False
    finally:
        await engine.dispose()


def _receipt(key, detail, *, issued_at=None, jti=None):
    now = int(datetime.now(UTC).timestamp()) if issued_at is None else issued_at
    return jwt.encode(
        {
            "iss": "slcs-test-signer",
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 120,
            "jti": jti or uuid.uuid4().hex,
            "v": 1,
            "receipt": {
                **{name: detail[name] for name in ("lesson_id", "revision_id", "fingerprint_version", "fingerprint")},
                "review_sha256": detail["review"]["review_sha256"],
            },
        },
        key,
        algorithm="EdDSA",
        headers={"kid": "test-only", "typ": TOKEN_TYPE},
    )


@pytest.mark.asyncio
async def test_signed_publication_is_idempotent_and_withdrawal_retains_progress(lesson_db, monkeypatch):
    sessions, concurrent = lesson_db
    document = json.loads(REFERENCE.read_bytes())
    lesson_id = document["lesson_id"] = f"slcs-test-{uuid.uuid4().hex}"
    document["media"] = {
        **document["media"],
        "access_mode": "provider_embed",
        "source_url": "https://youtube.com/watch?v=abcdefghijk",
    }
    key = Ed25519PrivateKey.generate()
    settings = get_settings()
    monkeypatch.setattr(settings, "slcs_lessons_enabled", False)
    async with sessions() as db:
        with pytest.raises(AppError) as disabled:
            await lessons.require_lessons_ready(db)
        assert disabled.value.status_code == 503
    monkeypatch.setattr(settings, "slcs_lessons_enabled", True)
    monkeypatch.setattr(settings, "slcs_lesson_receipt_issuer", "slcs-test-signer")
    pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    monkeypatch.setattr(settings, "slcs_lesson_receipt_public_keys", {"test-only": pem.decode()})

    async with sessions.begin() as db:
        await lessons.require_lessons_ready(db)
        admin, learner = User(role=RoleType.admin), User(role=RoleType.user)
        db.add_all([admin, learner])
        await db.flush()
        actor_id, learner_id = admin.id, learner.id

    async def import_pack(operation_id, payload):
        async with sessions.begin() as db:
            return await lessons.import_lesson(db, actor_id, operation_id, payload)

    async def review(detail, operation_id):
        body = ReviewLesson.model_validate(
            {
                "operation_id": operation_id,
                "source_commit": "a" * 40,
                "uses": {
                    "site_display": {"approved": True, "evidence": "synthetic test attestation"},
                    "model_processing": {"approved": False, "evidence": "not requested"},
                    "external_redistribution": {"approved": False, "evidence": "not requested"},
                },
            }
        )
        async with sessions.begin() as db:
            return await lessons.review_lesson(db, actor_id, lesson_id, detail["revision_id"], body)

    async def publish(detail, operation_id, receipt, expected=None):
        body = PublishLesson(operation_id=operation_id, expected_current_revision_id=expected, receipt=receipt)
        async with sessions.begin() as db:
            return await lessons.publish_lesson(db, actor_id, lesson_id, detail["revision_id"], body)

    payload = json.dumps(document).encode()
    if concurrent:
        original, duplicate = await asyncio.gather(import_pack("import-1", payload), import_pack("import-2", payload))
    else:
        original, duplicate = await import_pack("import-1", payload), await import_pack("import-2", payload)
    assert original["revision_id"] == duplicate["revision_id"]
    assert (await import_pack("import-1", payload))["replayed"]
    with pytest.raises(AppError) as invalid_pack:
        await import_pack("duplicate-keys", b'{"lesson_id":"one","lesson_id":"two"}')
    assert invalid_pack.value.detail[0]["path"] == "/"

    original_id = original["revision_id"]
    async with sessions() as db:
        assert (
            await db.scalar(
                select(func.count()).select_from(LessonRevision).where(LessonRevision.lesson_id == lesson_id)
            )
            == 1
        )
        with pytest.raises(AppError) as candidate:
            await lessons.get_visible_revision(db, lesson_id, original_id)
        assert candidate.value.status_code == 404

    original = await review(original, "review-1")
    signed = _receipt(key, original)
    with pytest.raises(AppError) as invalid_signature:
        await publish(original, "publish-1", _receipt(Ed25519PrivateKey.generate(), original))
    assert invalid_signature.value.status_code == 422
    async with sessions() as db:
        assert (await db.get(Lesson, lesson_id)).current_revision_id is None
    with pytest.raises(AppError) as expired_signature:
        await publish(original, "publish-1", _receipt(key, original, issued_at=1))
    assert expired_signature.value.status_code == 422
    tampered = {**original, "review": {**original["review"], "review_sha256": "0" * 64}}
    with pytest.raises(AppError) as different_review:
        await publish(original, "publish-1", _receipt(key, tampered))
    assert different_review.value.status_code == 422
    assert (await publish(original, "publish-1", signed))["status"] == "published"
    assert (await publish(original, "publish-1", signed))["replayed"]

    async with sessions.begin() as db:
        assert (await lessons.get_visible_revision(db, lesson_id)).id == original_id
        with pytest.raises(AppError) as display_only:
            await lessons.get_visible_revision(db, lesson_id, original_id, use="model_processing")
        assert display_only.value.status_code == 403
        await lesson_progress.save_progress(
            db, learner_id, lesson_id, SaveLessonProgress(revision_id=original_id, position_ms=650)
        )
        activity = RecordLessonActivity(
            revision_id=original_id, event_id="same-activity", event_type="watch_time", delta_s=12.0
        )
        for _ in range(2):
            result = await lesson_progress.record_activity(db, learner_id, lesson_id, activity)
            assert result["watch_seconds"] == 12.0
        now = datetime.now(UTC)
        seconds = await watch_seconds_by_local_day(
            db, learner_id, start=now - timedelta(hours=1), end=now + timedelta(hours=1), tz=ZoneInfo("UTC")
        )
        assert sum(seconds.values()) == 12
        # Course learning must reach the learning profile too: "days studied",
        # the streak and the weekly totals all read LearningEvent.
        events = list(await db.scalars(select(LearningEvent).where(LearningEvent.user_id == learner_id)))
        assert {event.event_type for event in events} == {"watched_video"}

    candidates = []
    for i in (2, 3):
        update = await import_pack(f"import-{i + 1}", json.dumps({**document, "title": f"Revised title {i}"}).encode())
        candidates.append(await review(update, f"review-{i}"))
    if concurrent:
        results = await asyncio.gather(
            *(publish(item, f"publish-{i}", _receipt(key, item), original_id) for i, item in enumerate(candidates, 2)),
            return_exceptions=True,
        )
        assert sorted(item.status_code if isinstance(item, AppError) else 200 for item in results) == [200, 409]
        winner = next(item for item in results if isinstance(item, dict))
    else:
        winner = await publish(candidates[0], "publish-2", _receipt(key, candidates[0]), original_id)
        with pytest.raises(AppError) as stale:
            await publish(candidates[1], "publish-3", _receipt(key, candidates[1]), original_id)
        assert stale.value.status_code == 409

    async with sessions.begin() as db:
        assert (await lessons.get_visible_revision(db, lesson_id, original_id)).id == original_id
        assert (await lessons.get_visible_revision(db, lesson_id)).id == winner["revision_id"]
        withdrawn_detail = await lessons.withdraw_lesson(
            db,
            actor_id,
            lesson_id,
            original_id,
            WithdrawLesson(operation_id="withdraw-1", reason="test withdrawal"),
        )
        # The maintainer still sees what was published; only public routes stop
        # serving it. Restoring needs the content and the unchanged review.
        assert withdrawn_detail["status"] == "withdrawn"
        assert withdrawn_detail["pack"]["lesson_id"] == lesson_id
    async with sessions() as db:
        with pytest.raises(AppError) as withdrawn:
            await lessons.get_visible_revision(db, lesson_id, original_id)
        assert withdrawn.value.status_code == 410
        assert withdrawn.value.code == "LESSON_WITHDRAWN"
        assert (await lesson_progress.read_progress(db, learner_id, lesson_id))["position_ms"] == 650
        history = await lesson_progress.read_history(db, learner_id, offset=0, limit=20)
        assert history[0]["revision_id"] == original_id
        assert history[0]["title"] is None and history[0]["available"] is False
        assert not await lesson_progress.read_history(db, actor_id, offset=0, limit=20)
        export = await _gather_lesson_data(db, learner_id)
        assert export["lesson_progress"][0]["revision_id"] == original_id
        assert export["lesson_activities"][0]["delta_s"] == 12.0
        assert "segments" not in json.dumps(export)
        assert (await lessons.get_visible_revision(db, lesson_id)).id == winner["revision_id"]
    async with sessions.begin() as db:
        await lessons.withdraw_lesson(
            db,
            actor_id,
            lesson_id,
            winner["revision_id"],
            WithdrawLesson(operation_id="withdraw-2", reason="test withdrawal"),
        )
    # Restore must be an explicit publish of the withdrawn revision, with a fresh
    # receipt, and the returned state must be usable again.
    restored = await publish(original, "publish-restore", _receipt(key, original))
    assert restored["status"] == "published"
    assert restored["pack"]["lesson_id"] == lesson_id
    with pytest.raises(AppError) as already_current:
        await publish(original, "publish-restore-2", _receipt(key, original))
    assert already_current.value.status_code == 409
    async with sessions() as db:
        assert (await lessons.get_visible_revision(db, lesson_id)).id == original_id
    async with sessions.begin() as db:
        await lessons.withdraw_lesson(
            db,
            actor_id,
            lesson_id,
            original_id,
            WithdrawLesson(operation_id="withdraw-3", reason="test withdrawal"),
        )
    async with sessions.begin() as db:
        assert (await db.get(Lesson, lesson_id)).current_revision_id is None
        assert all(item["lesson_id"] != lesson_id for item in await lessons.list_lessons(db))
        if concurrent:
            # The in-memory SQLite test database does not enforce foreign keys, so
            # ON DELETE CASCADE only proves anything on Postgres. The account purge
            # covers these tables explicitly; that path is tested separately.
            await db.execute(delete(User).where(User.id == learner_id))
            assert await db.get(LessonProgress, (learner_id, lesson_id), populate_existing=True) is None
            assert (
                await db.scalar(
                    select(func.count()).select_from(LessonActivity).where(LessonActivity.user_id == learner_id)
                )
                == 0
            )

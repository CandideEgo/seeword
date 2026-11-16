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
from app.models.lesson import Lesson, LessonActivity, LessonOperation, LessonProgress, LessonRevision
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
                "verification_method": "synthetic fixture comparison, not real listening evidence",
                "limitations": "test attestation only",
                "human_minutes": None,
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
    unused_before_withdrawal = _receipt(key, original)
    assert original["review"]["human_minutes"] is None
    assert "verification_method" not in original["pack"]
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

    # Ordinary rollback is the original CAS publication path, not a restoration
    # and not a new review. A stale CAS must not consume the operation or receipt.
    rollback_token = _receipt(key, original)
    with pytest.raises(AppError) as stale_rollback:
        await publish(original, "rollback", rollback_token, None)
    assert stale_rollback.value.status_code == 409
    reused_jti = jwt.decode(signed, options={"verify_signature": False})["jti"]
    with pytest.raises(AppError) as used_receipt:
        await publish(original, "rollback", _receipt(key, original, jti=reused_jti), winner["revision_id"])
    assert used_receipt.value.status_code == 409
    assert used_receipt.value.code == "IDEMPOTENCY_CONFLICT"
    rollback = await publish(original, "rollback", rollback_token, winner["revision_id"])
    assert rollback["review"] == original["review"]
    assert not rollback["requires_review"]
    await publish(winner, "return-to-winner", _receipt(key, winner), original_id)

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
        # Admin access preserves the immutable pack, but the old approval no
        # longer authorizes publication in this withdrawal cycle.
        assert withdrawn_detail["status"] == "withdrawn"
        assert withdrawn_detail["requires_review"] is True
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
    # Neither an unused pre-withdrawal receipt nor minting a new JWT against the
    # old review is a fresh approval. Failures roll back operation/receipt claims.
    async with sessions() as db:
        operations_before = await db.scalar(select(func.count()).select_from(LessonOperation))
    for invalid in (signed, unused_before_withdrawal, _receipt(key, original)):
        with pytest.raises(AppError) as stale_approval:
            await publish(original, "publish-restore", invalid)
        assert stale_approval.value.status_code == 422
    replayed_review = await review(original, "review-1")
    assert replayed_review["replayed"] and replayed_review["requires_review"]
    assert replayed_review["review"]["review_sha256"] == original["review"]["review_sha256"]
    # Replaying a successful old publish also cannot bring the material back.
    assert (await publish(original, "publish-1", signed))["status"] == "withdrawn"
    async with sessions() as db:
        assert (await db.get(Lesson, lesson_id)).current_revision_id is None
        assert await db.scalar(select(func.count()).select_from(LessonOperation)) == operations_before

    fixed_time = datetime.now(UTC)

    class SameTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_time

    monkeypatch.setattr(lessons, "datetime", SameTime)
    reapproved = await review(original, "review-restore")
    assert not reapproved["requires_review"]
    assert reapproved["review"]["withdrawal_id"] == withdrawn_detail["review"]["required_withdrawal_id"]
    assert reapproved["review"]["review_operation_id"] != original["review"]["review_operation_id"]
    assert reapproved["review"]["review_sha256"] != original["review"]["review_sha256"]
    assert reapproved["pack"] == original["pack"]
    stale_restore_authorization = _receipt(key, reapproved)
    # A new review operation invalidates the previous review's unused receipt,
    # even with identical evidence. Identical operation retries remain stable.
    latest = await review(original, "review-restore-again")
    assert latest["review"]["review_sha256"] != reapproved["review"]["review_sha256"]
    assert (await review(original, "review-restore-again"))["review"] == latest["review"]
    for invalid in (unused_before_withdrawal, stale_restore_authorization):
        with pytest.raises(AppError) as old_hash:
            await publish(original, "publish-restore", invalid)
        assert old_hash.value.status_code == 422
    unused_restore = _receipt(key, latest)
    restored = await publish(latest, "publish-restore", _receipt(key, latest))
    assert restored["status"] == "published"
    assert restored["pack"]["lesson_id"] == lesson_id
    with pytest.raises(AppError) as already_current:
        await publish(latest, "publish-restore-2", _receipt(key, latest))
    assert already_current.value.status_code == 409
    async with sessions() as db:
        assert (await lessons.get_visible_revision(db, lesson_id)).id == original_id
        progress = await lesson_progress.read_progress(db, learner_id, lesson_id)
        assert progress["position_ms"] == 650 and progress["watch_seconds"] == 12.0
    async with sessions.begin() as db:
        withdrawn_again = await lessons.withdraw_lesson(
            db,
            actor_id,
            lesson_id,
            original_id,
            WithdrawLesson(operation_id="withdraw-3", reason="test withdrawal"),
        )
    assert withdrawn_again["requires_review"]
    assert withdrawn_again["review"]["required_withdrawal_id"] != latest["review"]["withdrawal_id"]
    with pytest.raises(AppError) as prior_cycle:
        await publish(latest, "restore-second-cycle", unused_restore)
    assert prior_cycle.value.status_code == 422
    second_cycle = await review(latest, "review-second-cycle")
    assert second_cycle["review"]["withdrawal_id"] == withdrawn_again["review"]["required_withdrawal_id"]
    with pytest.raises(AppError) as prior_cycle_after_review:
        await publish(second_cycle, "restore-second-cycle", unused_restore)
    assert prior_cycle_after_review.value.status_code == 422
    await publish(second_cycle, "restore-second-cycle", _receipt(key, second_cycle))
    async with sessions.begin() as db:
        await lessons.withdraw_lesson(
            db, actor_id, lesson_id, original_id, WithdrawLesson(operation_id="withdraw-final", reason="finish test")
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


@pytest.mark.parametrize("with_withdrawal_audit", [True, False])
async def test_legacy_withdrawal_needs_auditable_new_review(lesson_db, with_withdrawal_audit):
    sessions, _ = lesson_db
    document = json.loads(REFERENCE.read_bytes())
    lesson_id = document["lesson_id"] = f"legacy-{uuid.uuid4().hex}"
    body = ReviewLesson(
        operation_id="legacy-new-review",
        source_commit="a" * 40,
        uses={
            use: {"approved": use == "site_display", "evidence": "synthetic legacy test"}
            for use in ("site_display", "model_processing", "external_redistribution")
        },
    )
    async with sessions.begin() as db:
        admin = User(role=RoleType.admin)
        db.add(admin)
        await db.flush()
        actor_id = admin.id
        imported = await lessons.import_lesson(db, actor_id, "legacy-import", json.dumps(document).encode())
        revision_id = imported["revision_id"]
        revision = await db.get(LessonRevision, revision_id)
        revision.status = "withdrawn"
        # Pre-P1 review JSON has neither withdrawal marker nor review operation.
        revision.review = {**body.model_dump(exclude={"operation_id"}), "review_sha256": "b" * 64}
        if with_withdrawal_audit:
            older = LessonOperation(
                actor_id=actor_id,
                operation_id="legacy-withdraw-older",
                action="withdraw",
                request_hash="c" * 64,
                revision_id=revision_id,
                created_at=datetime.now(UTC) - timedelta(days=1),
            )
            latest = LessonOperation(
                actor_id=actor_id,
                operation_id="legacy-withdraw-latest",
                action="withdraw",
                request_hash="d" * 64,
                revision_id=revision_id,
            )
            db.add_all([older, latest])
            await db.flush()
            latest_withdrawal_id = latest.id
    async with sessions() as db:
        assert (await lessons.admin_detail(db, lesson_id, revision_id))["requires_review"]
    with pytest.raises(AppError) as old_approval:
        async with sessions.begin() as db:
            await lessons.publish_lesson(
                db,
                actor_id,
                lesson_id,
                revision_id,
                PublishLesson(operation_id="legacy-restore", expected_current_revision_id=None, receipt="old-receipt"),
            )
    assert old_approval.value.status_code == 422

    async def review():
        async with sessions.begin() as db:
            return await lessons.review_lesson(db, actor_id, lesson_id, revision_id, body)

    if with_withdrawal_audit:
        approved = await review()
        assert not approved["requires_review"]
        assert approved["review"]["withdrawal_id"] == latest_withdrawal_id
        assert approved["review"]["required_withdrawal_id"] == latest_withdrawal_id
        assert approved["review"]["review_operation_id"]
        assert approved["review"]["review_sha256"] != "b" * 64
    else:
        with pytest.raises(AppError) as unauditable:
            await review()
        assert unauditable.value.status_code == 409
        async with sessions() as db:
            assert (await lessons.admin_detail(db, lesson_id, revision_id))["requires_review"]
            assert await db.scalar(select(func.count()).select_from(LessonOperation)) == 1

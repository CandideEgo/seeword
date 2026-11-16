"""Delegated learning: no facts before confirmation, explicit grants and replay fences."""

import asyncio
import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.dependencies import get_current_user
from app.api.v1 import delegated_learning as http_learning
from app.api.v1 import external_connections as http_connections
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.models.delegated_learning import ExternalLearningGrant, ExternalLearningIntent, ExternalLearningOperation
from app.models.learning import Vocabulary
from app.models.lesson import LessonActivity, LessonProgress
from app.models.lesson_learning import LessonVocabularySource, VocabularyReviewLog
from app.models.user import User
from app.schemas.delegated_learning import ConfirmIntent, PrepareIntent, ResourceLimits, SaveProgress, SaveVocabulary
from app.schemas.lesson import SaveLessonProgress
from app.services import delegated_learning as learning
from app.services import external_connection_service as connections
from app.services import lesson_progress
from app.services.teaching.principal import Principal
from tests.open_learning_fixtures import add_revision, fixed_reference

ALL_SCOPES = [
    "materials:read",
    "learning:vocabulary:write",
    "learning:progress:read",
    "learning:progress:write",
    "review:read",
    "review:write",
]


@pytest.fixture(autouse=True)
def enable(monkeypatch):
    settings = get_settings()
    for flag in ("mcp_read_enabled", "mcp_write_enabled", "slcs_lessons_enabled", "slcs_vocabulary_enabled"):
        monkeypatch.setattr(settings, flag, True)
    monkeypatch.setattr(settings, "teaching_allowed_user_ids", "learner,other")
    monkeypatch.setattr("app.services.ecdict.lookup", lambda _word: None)


async def seed(db, *, model=True, audience="model"):
    db.add_all([User(id="learner", phone="13900007201"), User(id="other", phone="13900007202")])
    revision = await add_revision(db, model=model)
    await db.flush()
    issued = await connections.create(
        db,
        "learner",
        "Synthetic helper",
        ALL_SCOPES,
        ResourceLimits(lesson_ids=[revision.lesson_id]),
        audience=audience,
    )
    await db.commit()
    return revision, issued


async def principal(db, issued, *, write=True):
    return await connections.authenticate(db, issued["token"], write=write)


async def save_word(db, issued, revision, operation_id="save"):
    return await learning.save_vocabulary(
        db, await principal(db, issued), SaveVocabulary(operation_id=operation_id, reference=fixed_reference(revision))
    )


async def count(db, model):
    return await db.scalar(select(func.count()).select_from(model))


async def test_continuous_save_replay_conflict_namespace_and_reprojection(db_session):
    revision, issued = await seed(db_session)
    first = await save_word(db_session, issued, revision)
    await db_session.commit()
    assert first == await save_word(db_session, issued, revision)
    assert await count(db_session, Vocabulary) == await count(db_session, LessonVocabularySource) == 1
    assert await count(db_session, ExternalLearningOperation) == 1
    with pytest.raises(AppError) as conflict:
        await learning.save_vocabulary(
            db_session,
            await principal(db_session, issued),
            SaveVocabulary(
                operation_id="save", reference={**fixed_reference(revision), "token_ids": ["w02"], "segment_id": "s02"}
            ),
        )
    assert conflict.value.status_code == 409
    another = await connections.create(
        db_session, "learner", "Other helper", ALL_SCOPES, ResourceLimits(lesson_ids=[revision.lesson_id])
    )
    await db_session.commit()
    assert (await save_word(db_session, another, revision))["word_id"] == first["word_id"]
    await db_session.commit()
    assert await count(db_session, ExternalLearningOperation) == 2
    revision.status = "withdrawn"
    await db_session.commit()
    with pytest.raises(AppError) as withdrawn:
        await save_word(db_session, issued, revision)
    assert withdrawn.value.status_code == 410
    receipts = list(await db_session.scalars(select(ExternalLearningOperation)))
    assert all("sentence" not in row.result and "word" not in row.result for row in receipts)


async def test_review_prepare_confirm_execute_once_and_current_permissions(db_session):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    await db_session.commit()
    body = PrepareIntent(operation_id="review-1", action="review", word_id=saved["word_id"], quality=5)
    pending = await learning.prepare_intent(db_session, await principal(db_session, issued), body)
    await db_session.commit()
    assert pending["confirmation_url"] == "/profile?tab=account#learning-intents"
    assert pending["status"] == "pending" and await count(db_session, VocabularyReviewLog) == 0
    assert pending["id"] == (await learning.prepare_intent(db_session, await principal(db_session, issued), body))["id"]
    with pytest.raises(AppError) as unconfirmed:
        await learning.execute_intent(db_session, await principal(db_session, issued), pending["id"])
    assert unconfirmed.value.code == "CONFIRMATION_REQUIRED"
    assert await count(db_session, VocabularyReviewLog) == 0
    with pytest.raises(AppError) as changed:
        await learning.prepare_intent(
            db_session, await principal(db_session, issued), body.model_copy(update={"quality": 2})
        )
    assert changed.value.status_code == 409
    view = (await learning.list_intents(db_session, "learner"))["items"][0]
    assert view["resource"]["word"] == "public domain" and view["resource"]["available"] is True
    assert await learning.list_intents(db_session, "other") == {"items": []}
    with pytest.raises(AppError) as foreign:
        await learning.confirm_intent(db_session, "other", pending["id"])
    assert foreign.value.status_code == 404
    assert (await learning.confirm_intent(db_session, "learner", pending["id"]))["status"] == "approved"
    await db_session.commit()
    result = await learning.execute_intent(db_session, await principal(db_session, issued), pending["id"])
    await db_session.commit()
    assert result == await learning.execute_intent(db_session, await principal(db_session, issued), pending["id"])
    assert result["review_count"] == 1
    assert await count(db_session, VocabularyReviewLog) == 1
    revision.status = "withdrawn"
    await db_session.commit()
    with pytest.raises(AppError) as withdrawn:
        await learning.execute_intent(db_session, await principal(db_session, issued), pending["id"])
    assert withdrawn.value.status_code == 404
    assert await count(db_session, VocabularyReviewLog) == 1


async def test_completion_intent_and_progress_cas_track_first_party_writes(db_session):
    revision, issued = await seed(db_session)
    p = await principal(db_session, issued)
    assert (await learning.read_progress(db_session, p, revision.lesson_id))["version"] == "0"
    body = SaveProgress(operation_id="position", revision_id=revision.id, position_ms=200, expected_version="0")
    first = await learning.save_progress(db_session, p, revision.lesson_id, body)
    await db_session.commit()
    assert "+00:00" in first["version"]
    website = await lesson_progress.save_progress(
        db_session, "learner", revision.lesson_id, SaveLessonProgress(revision_id=revision.id, position_ms=400)
    )
    await db_session.commit()
    assert website["version"] > first["version"]
    with pytest.raises(AppError) as stale:
        await learning.save_progress(
            db_session,
            await principal(db_session, issued),
            revision.lesson_id,
            body.model_copy(update={"operation_id": "stale", "expected_version": first["version"]}),
        )
    assert stale.value.status_code == 409
    await db_session.rollback()
    await db_session.refresh(revision)
    assert (
        await learning.save_progress(db_session, await principal(db_session, issued), revision.lesson_id, body) == first
    )
    current = await learning.read_progress(db_session, await principal(db_session, issued), revision.lesson_id)
    assert current["position_ms"] == 400 and current["version"] == website["version"]
    intent = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(
            operation_id="complete", action="complete", lesson_id=revision.lesson_id, revision_id=revision.id
        ),
    )
    assert await count(db_session, LessonActivity) == 0
    assert not (await db_session.get(LessonProgress, ("learner", revision.lesson_id))).completed
    await learning.confirm_intent(db_session, "learner", intent["id"])
    result = await learning.execute_intent(db_session, await principal(db_session, issued), intent["id"])
    await db_session.commit()
    assert result["completed"] is True and result["version"] > website["version"]
    assert result == await learning.execute_intent(db_session, await principal(db_session, issued), intent["id"])
    assert await count(db_session, LessonActivity) == 1


async def test_expiry_cross_connection_revocation_and_rotation(db_session):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    pending = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="review", action="review", word_id=saved["word_id"], quality=2),
    )
    second = await connections.create(
        db_session, "learner", "Another", ALL_SCOPES, ResourceLimits(lesson_ids=[revision.lesson_id])
    )
    await db_session.commit()
    with pytest.raises(AppError) as cross_connection:
        await learning.execute_intent(db_session, await principal(db_session, second), pending["id"])
    assert cross_connection.value.status_code == 404
    row = await db_session.get(ExternalLearningIntent, pending["id"])
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()
    with pytest.raises(AppError) as expired:
        await learning.confirm_intent(db_session, "learner", pending["id"])
    assert expired.value.status_code == 409
    assert await learning.cleanup_expired_intents(db_session) == 1
    assert await count(db_session, ExternalLearningOperation) == 1
    replacement = await connections.rotate(db_session, "learner", issued["connection"]["id"])
    await db_session.commit()
    with pytest.raises(AppError) as rotated:
        await principal(db_session, issued)
    assert rotated.value.status_code == 401
    await connections.revoke(db_session, "learner", replacement["connection"]["id"])
    await db_session.commit()
    with pytest.raises(AppError) as revoked:
        await principal(db_session, replacement)
    assert revoked.value.status_code == 401
    assert await count(db_session, ExternalLearningOperation) == 1


async def test_due_queue_filters_before_paging_and_uses_shared_schedule(db_session):
    revision, issued = await seed(db_session, model=False, audience="application")
    course_word = await save_word(db_session, issued, revision)
    word = await db_session.get(Vocabulary, course_word["word_id"])
    word.mastery_level = "reviewing"
    db_session.add_all(
        [
            Vocabulary(id="private", user_id="learner", word="private-secret", mastery_level="reviewing"),
            Vocabulary(
                id="explicit", user_id="learner", word="allowed", mastery_level="reviewing", next_review_at=None
            ),
            Vocabulary(id="new", user_id="learner", word="unlearned", mastery_level="new"),
            Vocabulary(id="mastered", user_id="learner", word="finished", mastery_level="mastered"),
            Vocabulary(id="foreign", user_id="other", word="foreign-secret", mastery_level="reviewing"),
        ]
    )
    await db_session.flush()
    readonly = await connections.create(
        db_session,
        "learner",
        "Explicit review",
        ["review:read"],
        ResourceLimits(word_ids=["explicit", "new", "mastered"]),
    )
    await db_session.commit()
    result = await learning.review_tasks(db_session, await principal(db_session, readonly, write=False), limit=1)
    assert result["total"] == 1 and result["items"][0]["id"] == "explicit"
    assert result["items"][0]["resume_url"] == "/vocabulary/review"
    assert "secret" not in str(result)
    model_connection = await connections.create(
        db_session, "learner", "Model review", ALL_SCOPES, ResourceLimits(lesson_ids=[revision.lesson_id])
    )
    await db_session.commit()
    assert (await learning.review_tasks(db_session, await principal(db_session, model_connection), model=True))[
        "total"
    ] == 0
    assert (await learning.review_tasks(db_session, await principal(db_session, model_connection)))["total"] == 0
    with pytest.raises(AppError) as wrong_audience:
        await learning.review_tasks(db_session, await principal(db_session, issued), model=True)
    assert wrong_audience.value.status_code == 403
    assert (await learning.review_tasks(db_session, await principal(db_session, issued)))["total"] == 1
    revision.status = "withdrawn"
    await db_session.commit()
    assert (await learning.review_tasks(db_session, await principal(db_session, issued)))["total"] == 0


async def test_resource_scope_and_model_disclosure_denials(db_session):
    revision, issued = await seed(db_session, model=False, audience="application")
    with pytest.raises(AppError) as model_denied:
        await learning.save_vocabulary(
            db_session,
            await principal(db_session, issued),
            SaveVocabulary(operation_id="model-denied", reference=fixed_reference(revision)),
            model=True,
        )
    assert model_denied.value.status_code == 403
    assert await count(db_session, Vocabulary) == 0
    other = await add_revision(db_session, "another", "Private other title")
    with pytest.raises(AppError) as ungranted:
        await save_word(db_session, issued, other)
    assert ungranted.value.status_code == 404
    for scopes in (["learning:vocabulary:write"], ["learning:progress:write"], ["review:write"]):
        with pytest.raises(AppError) as dependency:
            await connections.create(
                db_session, "learner", "Bad scopes", scopes, ResourceLimits(lesson_ids=[revision.lesson_id])
            )
        assert dependency.value.status_code == 422
    legacy = await connections.create(db_session, "learner", "Legacy", ["teaching:read", "review:read"])
    await db_session.commit()
    assert legacy["connection"]["resource_limits"] == {}
    assert (await learning.review_tasks(db_session, await principal(db_session, legacy)))["items"] == []
    with pytest.raises(AppError) as missing_scope:
        await save_word(db_session, legacy, revision)
    assert missing_scope.value.status_code == 403
    with pytest.raises(AppError) as forged_identity:
        await learning.read_progress(db_session, Principal("learner"), revision.lesson_id)
    assert forged_identity.value.status_code == 403


@pytest.mark.parametrize(
    "extra",
    [
        {"confirmed": True},
        {"user_id": "other"},
        {"quality": True},
        {"quality": "5"},
        {"lesson_id": "unrelated"},
        {"audience": "application"},
    ],
)
def test_prepare_rejects_self_reported_confirmation_and_free_parameters(extra):
    with pytest.raises(ValidationError):
        PrepareIntent(**{"operation_id": "test", "action": "review", "word_id": "owned", "quality": 5, **extra})


@pytest.mark.parametrize(
    "body", [{"confirmed": False}, {"confirmed": 1}, {"confirmed": "true"}, {"confirmed": True, "quality": 5}]
)
def test_confirm_requires_strict_first_party_affirmation(body):
    with pytest.raises(ValidationError):
        ConfirmIntent(**body)


def test_grant_bounds_and_explicit_resources():
    for body in ({}, {"word_ids": ["a"] * 2}, {"lesson_ids": [f"l{x}" for x in range(201)]}):
        with pytest.raises(ValidationError):
            ResourceLimits(**body)


async def test_missing_learning_tables_leave_legacy_teaching_auth_working(db_session):
    _revision, issued = await seed(db_session)
    legacy = await connections.create(db_session, "learner", "Legacy", ["teaching:read"])
    await db_session.commit()
    connection = await db_session.connection()
    await connection.run_sync(lambda sync: ExternalLearningOperation.__table__.drop(sync))
    assert (await principal(db_session, legacy)).granted_scopes == frozenset({"teaching:read"})
    with pytest.raises(AppError) as unmigrated:
        await principal(db_session, issued)
    assert unmigrated.value.status_code == 503
    assert (await learning.export_sections(db_session, "learner"))["external_learning_operations"] == []
    await learning.purge_facts(db_session, "learner")


async def test_export_and_purge_are_user_scoped_and_exclude_hashes(db_session):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="review", action="review", word_id=saved["word_id"], quality=5),
    )
    await connections.create(
        db_session, "other", "Other account", ["materials:read"], ResourceLimits(lesson_ids=[revision.lesson_id])
    )
    await db_session.commit()
    exported = await learning.export_sections(db_session, "learner")
    text = json.dumps(exported, default=str)
    assert "payload_hash" not in text and '"token"' not in text and "token_hash" not in text and "sentence" not in text
    assert len(exported["external_learning_operations"]) == len(exported["external_learning_intents"]) == 1
    assert all(row["user_id"] == "learner" for rows in exported.values() for row in rows)
    await learning.purge_facts(db_session, "learner")
    await db_session.commit()
    assert await count(db_session, ExternalLearningOperation) == await count(db_session, ExternalLearningIntent) == 0
    remaining = list(await db_session.scalars(select(ExternalLearningGrant)))
    assert len(remaining) == 1 and remaining[0].user_id == "other"


async def test_http_opaque_auth_strict_confirm_and_empty_execute_body(db_session):
    revision, issued = await seed(db_session)
    app = FastAPI()
    app.include_router(http_learning.router, prefix="/api/v1")
    app.include_router(http_connections.router, prefix="/api/v1")

    async def db_override():
        yield db_session

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = lambda: User(id="learner")
    from starlette.responses import JSONResponse

    @app.exception_handler(AppError)
    async def app_error(_request, exc):
        return JSONResponse({"code": str(exc.code), "message": exc.message}, status_code=exc.status_code)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        url = "/api/v1/external-learning"
        assert (await client.get(url + "/materials")).status_code == 401
        assert (
            await client.get(url + "/materials", headers={"Authorization": "Bearer JWT-not-opaque"})
        ).status_code == 401
        headers = {"Authorization": "Bearer " + issued["token"]}
        assert (await client.get(url + "/materials", headers=headers)).json()["total"] == 1
        overflow = await client.put(
            url + f"/lessons/{revision.lesson_id}/progress",
            headers=headers,
            json={
                "operation_id": "overflow",
                "revision_id": revision.id,
                "position_ms": 2**63,
                "expected_version": "0",
            },
        )
        assert overflow.status_code == 422
        assert await count(db_session, LessonProgress) == 0
        assert await count(db_session, ExternalLearningOperation) == 0
        saved = await client.post(
            url + "/vocabulary", headers=headers, json={"operation_id": "save", "reference": fixed_reference(revision)}
        )
        assert saved.status_code == 200, saved.text
        pending = await client.post(
            url + "/intents",
            headers=headers,
            json={"operation_id": "review", "action": "review", "word_id": saved.json()["word_id"], "quality": 5},
        )
        assert pending.status_code == 201, pending.text
        intent_id = pending.json()["id"]
        assert (
            await client.post(url + f"/intents/{intent_id}/execute", headers=headers, json={"confirmed": True})
        ).status_code == 422
        confirm_url = f"/api/v1/external-connections/learning-intents/{intent_id}/confirm"
        assert (await client.post(confirm_url, json={"confirmed": "true"})).status_code == 422
        assert (await client.post(confirm_url, json={"confirmed": True})).status_code == 200
        assert (await client.post(url + f"/intents/{intent_id}/execute", headers=headers)).status_code == 200
        assert await count(db_session, VocabularyReviewLog) == 1
        # A model grant cannot downgrade its purpose by taking the REST path or
        # inventing per-request audience/model query parameters.
        revision.review = {
            **revision.review,
            "uses": {**revision.review["uses"], "model_processing": {"approved": False}},
        }
        await db_session.commit()
        assert (await client.get(url + "/materials?audience=application&model=false", headers=headers)).json()[
            "total"
        ] == 0
        blocked = await client.post(
            url + "/context?audience=application&model=false", headers=headers, json=fixed_reference(revision)
        )
        assert blocked.status_code == 403 and "sentence" not in blocked.json()


async def test_application_audience_is_explicit_and_cannot_be_used_for_models(db_session):
    revision, model_connection = await seed(db_session, model=False)
    application = await connections.create(
        db_session,
        "learner",
        "Deterministic application",
        ALL_SCOPES,
        ResourceLimits(lesson_ids=[revision.lesson_id]),
        audience="application",
    )
    await db_session.commit()
    assert model_connection["connection"]["audience"] == "model"
    assert application["connection"]["audience"] == "application"
    model_principal = await principal(db_session, model_connection)
    app_principal = await principal(db_session, application)
    from app.services import lesson_catalog

    assert (await lesson_catalog.search_materials(db_session, model_principal))["total"] == 0
    assert (await lesson_catalog.search_materials(db_session, app_principal))["total"] == 1
    with pytest.raises(AppError) as denied_model_use:
        await lesson_catalog.search_materials(db_session, app_principal, model=True)
    assert denied_model_use.value.status_code == 403
    # A legacy grant without immutable audience metadata defaults to model,
    # including when the in-memory principal was previously application-scoped.
    grant = await db_session.get(ExternalLearningGrant, application["connection"]["id"])
    grant.resource_limits = {key: value for key, value in grant.resource_limits.items() if key != "disclosure_audience"}
    await db_session.commit()
    with pytest.raises(AppError) as stale_principal:
        await learning.save_vocabulary(
            db_session, app_principal, SaveVocabulary(operation_id="stale-purpose", reference=fixed_reference(revision))
        )
    assert stale_principal.value.status_code == 403
    assert await count(db_session, Vocabulary) == 0


async def test_bare_private_word_application_grant_does_not_allow_model_disclosure(db_session):
    _revision, _issued = await seed(db_session)
    db_session.add(Vocabulary(id="private-bare", user_id="learner", word="private-only", mastery_level="reviewing"))
    await db_session.flush()
    application = await connections.create(
        db_session,
        "learner",
        "Application only",
        ["review:read"],
        ResourceLimits(word_ids=["private-bare"]),
        audience="application",
    )
    await db_session.commit()
    app_principal = await principal(db_session, application, write=False)
    assert (await learning.review_tasks(db_session, app_principal))["items"][0]["word"] == "private-only"
    with pytest.raises(AppError) as model_use:
        await learning.review_tasks(db_session, app_principal, model=True)
    assert model_use.value.status_code == 403


async def test_failed_receipt_rolls_back_learning_fact_and_intent_consumption(db_session, monkeypatch):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    intent = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="atomic", action="review", word_id=saved["word_id"], quality=5),
    )
    await learning.confirm_intent(db_session, "learner", intent["id"])
    await db_session.commit()

    def broken_receipt(*_args, **_kwargs):
        raise RuntimeError("injected receipt write failure")

    monkeypatch.setattr(learning, "_receipt", broken_receipt)
    with pytest.raises(RuntimeError, match="injected"):
        await learning.execute_intent(db_session, await principal(db_session, issued), intent["id"])
    await db_session.rollback()
    assert await count(db_session, VocabularyReviewLog) == 0
    word = await db_session.get(Vocabulary, saved["word_id"])
    assert word.review_count == 0
    row = await db_session.get(ExternalLearningIntent, intent["id"])
    assert row.approved_at is not None and row.consumed_at is None
    assert await count(db_session, ExternalLearningOperation) == 1


async def test_unavailable_intent_hides_word_and_expired_status_is_explicit(db_session):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    intent = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="status", action="review", word_id=saved["word_id"], quality=5),
    )
    row = await db_session.get(ExternalLearningIntent, intent["id"])
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()
    assert (await learning.list_intents(db_session, "learner"))["items"][0]["status"] == "expired"
    revision.status = "withdrawn"
    await db_session.commit()
    view = (await learning.list_intents(db_session, "learner"))["items"][0]
    assert view["status"] == "unavailable" and view["resource"]["available"] is False
    assert "word" not in view["resource"] and "title" not in view["resource"]


async def test_consumed_intent_tombstone_replays_after_expiry_cleanup(db_session):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    pending = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="lost-response", action="review", word_id=saved["word_id"], quality=2),
    )
    await learning.confirm_intent(db_session, "learner", pending["id"])
    first = await learning.execute_intent(db_session, await principal(db_session, issued), pending["id"])
    await db_session.commit()
    row = await db_session.get(ExternalLearningIntent, pending["id"])
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()
    assert await learning.cleanup_expired_intents(db_session) == 0
    await db_session.commit()
    assert await learning.list_intents(db_session, "learner") == {"items": []}
    replay = await learning.execute_intent(db_session, await principal(db_session, issued), pending["id"])
    assert replay == first
    assert await count(db_session, VocabularyReviewLog) == 1
    assert await count(db_session, ExternalLearningOperation) == 2


async def test_intent_list_tolerates_cleanup_between_enumeration_and_lock(db_session, monkeypatch):
    revision, issued = await seed(db_session)
    saved = await save_word(db_session, issued, revision)
    expired = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="expired-list", action="review", word_id=saved["word_id"], quality=2),
    )
    active = await learning.prepare_intent(
        db_session,
        await principal(db_session, issued),
        PrepareIntent(operation_id="active-list", action="review", word_id=saved["word_id"], quality=5),
    )
    row = await db_session.get(ExternalLearningIntent, expired["id"])
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()
    original = learning._owned_intent

    async def interleaved(db, user_id, intent_id):
        if intent_id == expired["id"]:
            assert await learning.cleanup_expired_intents(db) == 1
            await db.commit()
        return await original(db, user_id, intent_id)

    monkeypatch.setattr(learning, "_owned_intent", interleaved)
    result = await learning.list_intents(db_session, "learner")
    assert [item["id"] for item in result["items"]] == [active["id"]]
    assert await count(db_session, VocabularyReviewLog) == 0


@pytest.mark.integration
async def test_pg_cross_user_and_unconfirmed_intents_never_write_facts():
    from tests.conftest import _pg_engine_or_skip

    sessions = async_sessionmaker(await _pg_engine_or_skip(), expire_on_commit=False)
    async with sessions() as db:
        revision, issued = await seed(db)
        saved = await save_word(db, issued, revision)
        intent = await learning.prepare_intent(
            db,
            await principal(db, issued),
            PrepareIntent(operation_id="unconfirmed", action="review", word_id=saved["word_id"], quality=5),
        )
        other = await connections.create(
            db, "other", "Other", ALL_SCOPES, ResourceLimits(lesson_ids=[revision.lesson_id])
        )
        await db.commit()
    async with sessions() as db:
        with pytest.raises(AppError) as foreign:
            await learning.execute_intent(db, await principal(db, other), intent["id"])
        assert foreign.value.status_code == 404
        with pytest.raises(AppError) as confirmation:
            await learning.confirm_intent(db, "other", intent["id"])
        assert confirmation.value.status_code == 404
    async with sessions() as db:
        with pytest.raises(AppError) as pending:
            await learning.execute_intent(db, await principal(db, issued), intent["id"])
        assert pending.value.code == "CONFIRMATION_REQUIRED"
        assert await count(db, VocabularyReviewLog) == 0


@pytest.mark.integration
async def test_pg_two_connections_cas_only_one_position_wins():
    from tests.conftest import _pg_engine_or_skip

    sessions = async_sessionmaker(await _pg_engine_or_skip(), expire_on_commit=False)
    async with sessions() as db:
        revision, first = await seed(db)
        lesson_id, revision_id = revision.lesson_id, revision.id
        second = await connections.create(db, "learner", "Second", ALL_SCOPES, ResourceLimits(lesson_ids=[lesson_id]))
        await db.commit()

    async def write(issued, position):
        try:
            async with sessions.begin() as db:
                return await learning.save_progress(
                    db,
                    await principal(db, issued),
                    lesson_id,
                    SaveProgress(
                        operation_id="position", revision_id=revision_id, position_ms=position, expected_version="0"
                    ),
                )
        except AppError as exc:
            return exc.status_code

    results = await asyncio.wait_for(asyncio.gather(write(first, 100), write(second, 200)), timeout=10)
    assert sum(isinstance(result, dict) for result in results) == 1 and 409 in results
    async with sessions() as db:
        assert await count(db, ExternalLearningOperation) == 1
        assert await count(db, LessonProgress) == 1


@pytest.mark.integration
async def test_pg_rotation_blocks_waiting_old_credential():
    from tests.conftest import _pg_engine_or_skip

    sessions = async_sessionmaker(await _pg_engine_or_skip(), expire_on_commit=False)
    async with sessions() as db:
        _revision, issued = await seed(db)
    started = asyncio.Event()

    async def authenticate_old():
        async with sessions.begin() as db:
            started.set()
            return await principal(db, issued)

    task = None
    try:
        async with sessions.begin() as db:
            replacement = await connections.rotate(db, "learner", issued["connection"]["id"])
            task = asyncio.create_task(authenticate_old())
            await started.wait()
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(task), timeout=0.05)
        with pytest.raises(AppError) as rotated:
            await asyncio.wait_for(task, timeout=5)
        assert rotated.value.status_code == 401
        async with sessions() as db:
            assert (await principal(db, replacement)).user_id == "learner"
    finally:
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


@pytest.mark.integration
async def test_pg_concurrent_duplicate_review_executes_once():
    from tests.conftest import _pg_engine_or_skip

    sessions = async_sessionmaker(await _pg_engine_or_skip(), expire_on_commit=False)
    async with sessions() as db:
        revision, issued = await seed(db)
        saved = await save_word(db, issued, revision)
        intent = await learning.prepare_intent(
            db,
            await principal(db, issued),
            PrepareIntent(operation_id="review", action="review", word_id=saved["word_id"], quality=5),
        )
        await learning.confirm_intent(db, "learner", intent["id"])
        await db.commit()

    async def execute():
        async with sessions.begin() as db:
            return await learning.execute_intent(db, await principal(db, issued), intent["id"])

    first, second = await asyncio.wait_for(asyncio.gather(execute(), execute()), timeout=10)
    assert first == second
    async with sessions() as db:
        assert await count(db, VocabularyReviewLog) == 1
        assert await count(db, ExternalLearningOperation) == 2


@pytest.mark.integration
async def test_pg_revoke_waits_for_transaction_then_replay_fails():
    from tests.conftest import _pg_engine_or_skip

    sessions = async_sessionmaker(await _pg_engine_or_skip(), expire_on_commit=False)
    async with sessions() as db:
        revision, issued = await seed(db)
        reference = fixed_reference(revision)
    started = asyncio.Event()

    async def revoke():
        async with sessions.begin() as db:
            started.set()
            await connections.revoke(db, "learner", issued["connection"]["id"])

    task = None
    try:
        async with sessions.begin() as db:
            p = await principal(db, issued)
            task = asyncio.create_task(revoke())
            await started.wait()
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(task), timeout=0.05)
            await learning.save_vocabulary(db, p, SaveVocabulary(operation_id="save", reference=reference))
        await asyncio.wait_for(task, timeout=5)
        async with sessions() as db:
            with pytest.raises(AppError) as denied:
                await principal(db, issued)
            assert denied.value.status_code == 401
            assert await count(db, ExternalLearningOperation) == 1
            assert await count(db, Vocabulary) == 1
    finally:
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

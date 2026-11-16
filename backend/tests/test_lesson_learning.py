"""Course anchors and model disclosure follow the live published revision."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.database import get_async_session_maker
from app.core.errors import AppError
from app.models.learning import Vocabulary
from app.models.learning_plan import LearningEvent
from app.models.lesson import Lesson, LessonRevision
from app.models.lesson_learning import LessonVocabularySource, VocabularyReviewLog
from app.models.user import User
from app.models.v2_runtime import TutorConversation
from app.services import lesson_learning, teaching_gateway, teaching_runs, vocabulary_service
from app.services.teaching import dialogue
from app.services.teaching.principal import Principal
from app.services.video_learning_material import load_video_material

PACK = Path(__file__).resolve().parents[2] / "docs" / "slcs" / "examples" / "welcome-to-wikisource.json"
SEGMENT, TOKENS = "s03", ["w04", "w05"]


async def seed(db, monkeypatch, *, model_allowed=True):
    settings = get_settings()
    for name in (
        "slcs_lessons_enabled",
        "slcs_tutor_enabled",
        "slcs_vocabulary_enabled",
        "teaching_dialogue_enabled",
        "teaching_runs_enabled",
        "teaching_streaming_enabled",
    ):
        monkeypatch.setattr(settings, name, True)
    monkeypatch.setattr(teaching_runs, "require_gateway", lambda: None)
    monkeypatch.setattr(lesson_learning.ecdict, "lookup", lambda _word: None)
    user = User(phone="13800001281", name="SLCS Learner")
    pack = json.loads(PACK.read_bytes())
    lesson = Lesson(id=pack["lesson_id"])
    db.add_all([user, lesson])
    await db.flush()
    monkeypatch.setattr(settings, "teaching_allowed_user_ids", user.id)
    revision = await published_revision(db, lesson.id, pack, model_allowed=model_allowed)
    await db.commit()
    return user.id, lesson.id, revision.id


async def published_revision(db, lesson_id, pack, *, model_allowed):
    material = load_video_material(json.dumps(pack, ensure_ascii=False).encode("utf-8"))
    revision = LessonRevision(
        lesson_id=lesson_id,
        fingerprint=material.source_fingerprint,
        fingerprint_version="slcs-pack-v1",
        title=pack["title"],
        access_mode=pack["media"]["access_mode"],
        pack=pack,
        status="published",
        review={"uses": {"site_display": {"approved": True}, "model_processing": {"approved": model_allowed}}},
    )
    db.add(revision)
    await db.flush()
    return revision


async def test_same_word_two_revisions_and_review_replay_after_withdrawal(db_session, monkeypatch):
    user, lesson, first_id = await seed(db_session, monkeypatch)
    other = User(phone="13800001282", name="Other Learner")
    # A legacy word without a source should acquire anchors without resetting the schedule.
    vocab = Vocabulary(user_id=user, word="public domain", review_count=3, mastery_level="reviewing")
    db_session.add_all([other, vocab])
    pack = json.loads(PACK.read_bytes())
    pack["title"] += " (updated)"
    second = await published_revision(db_session, lesson, pack, model_allowed=True)
    for revision_id in (first_id, first_id, second.id):
        saved = await lesson_learning.save_source(db_session, user, lesson, revision_id, SEGMENT, TOKENS)
        assert saved["word_id"] == vocab.id
        assert saved["source"]["start_ms"] == 13602
        assert saved["source"]["end_ms"] == 14242
    assert vocab.review_count == 3
    assert vocab.context_sentence is None
    await db_session.commit()

    with pytest.raises(AppError) as foreign:
        await lesson_learning.list_sources(db_session, other.id, vocab.id)
    assert foreign.value.status_code == 404
    assert await db_session.scalar(select(func.count(LessonVocabularySource.id))) == 2
    original = await db_session.get(LessonRevision, first_id)
    original.status = "withdrawn"
    second.status = "withdrawn"
    await db_session.commit()

    result = await lesson_learning.list_sources(db_session, user, vocab.id)
    assert {item["revision_id"] for item in result["sources"]} == {first_id, second.id}
    assert all(not item["available"] and item["start_ms"] is None for item in result["sources"])
    (word_view,) = await vocabulary_service.attach_word_sources(db_session, [vocab])
    assert word_view["has_lesson_sources"] and word_view["review_operations_enabled"]

    first = await vocabulary_service.record_idempotent_review(db_session, user, vocab.id, 5, "review-1")
    await db_session.commit()
    await vocabulary_service.record_idempotent_review(db_session, user, vocab.id, 1, "review-2")
    await db_session.commit()
    replay = await vocabulary_service.record_idempotent_review(db_session, user, vocab.id, 5, "review-1")
    assert replay == first
    assert vocab.review_count == 5
    with pytest.raises(AppError) as conflict:
        await vocabulary_service.record_idempotent_review(db_session, user, vocab.id, 4, "review-1")
    assert conflict.value.status_code == 409
    logs = list(await db_session.scalars(select(VocabularyReviewLog).where(VocabularyReviewLog.user_id == user)))
    assert len(logs) == 2
    assert all(vocabulary_service.replay_review(log) == log.after_state for log in logs)
    assert await db_session.scalar(select(func.count(LearningEvent.id)).where(LearningEvent.user_id == user)) == 2
    exported = await lesson_learning.export_sections(db_session, user)
    assert len(exported["lesson_vocabulary_sources"]) == len(exported["vocabulary_review_log"]) == 2


def tutor_input(revision_id):
    return SimpleNamespace(
        revision_id=revision_id,
        segment_id=SEGMENT,
        token_ids=TOKENS,
        request_id="tutor-turn-1",
        conversation_id=None,
        message="这里是什么意思？",
    )


async def test_tutor_reuses_durable_stream_and_redacts_old_history(db_session, monkeypatch):
    user, lesson, revision_id = await seed(db_session, monkeypatch)
    principal = Principal(user)
    body = tutor_input(revision_id)
    run = await teaching_runs.start_lesson_turn(db_session, principal, lesson, body)
    replay = await teaching_runs.start_lesson_turn(db_session, principal, lesson, body)
    assert run == replay
    await db_session.commit()
    seen = []

    async def stream(*_args, before_dispatch):
        context = await before_dispatch()
        payload = teaching_gateway._tutor_stream_messages(body.message, context)
        sent = json.loads(payload[-1]["content"])
        seen.extend(sent["sources"])
        assert set(sent["sources"][0]) == {"index", "text", "translation", "headword", "gloss"}
        assert sent["history"] == []
        yield {"type": "delta", "text": "这里指公有领域[1]。"}
        yield {"type": "done", "usage_status": "missing"}

    monkeypatch.setattr(teaching_gateway, "stream_tutor_reply", stream)
    await teaching_runs.execute(run["run_id"])
    assert len(seen) == 1
    page = await dialogue.page_lesson(db_session, principal, lesson, run["conversation_id"])
    assistant = page["items"][-1]
    assert assistant["role"] == "assistant"
    assert assistant["status"] == "complete"
    assert assistant["body"]["lesson_citation"]["token_ids"] == TOKENS
    assert assistant["body"]["lesson_citation"]["start_ms"] == 13602

    revision = await db_session.get(LessonRevision, revision_id)
    revision.status = "withdrawn"
    await db_session.commit()
    recovered = await dialogue.page_lesson(db_session, principal, lesson, run["conversation_id"])
    assert all(item["restricted"] and item["body"] is None and item["blocks"] == [] for item in recovered["items"])
    events, status = await teaching_runs.events(db_session, principal, run["run_id"], 0)
    assert status == "succeeded"
    assert any(event["type"] == "content.restricted" for event in events)
    assert all(event["type"] not in {"message.block", "message.upsert"} for event in events)
    _, exported = await dialogue.export_all(db_session, principal)
    assert all(item["restricted"] and item["body"] is None for item in exported)


async def test_display_only_revision_cannot_queue_a_model_run(db_session, monkeypatch):
    user, lesson, revision_id = await seed(db_session, monkeypatch, model_allowed=False)
    with pytest.raises(AppError) as denied:
        await teaching_runs.start_lesson_turn(db_session, Principal(user), lesson, tutor_input(revision_id))
    assert denied.value.status_code == 403


async def test_withdrawal_while_queued_prevents_provider_disclosure(db_session, monkeypatch):
    user, lesson, revision_id = await seed(db_session, monkeypatch)
    run = await teaching_runs.start_lesson_turn(db_session, Principal(user), lesson, tutor_input(revision_id))
    revision = await db_session.get(LessonRevision, revision_id)
    revision.status = "withdrawn"
    await db_session.commit()

    async def should_not_stream(*_args, **_kwargs):
        pytest.fail("the model stream started after withdrawal")

    monkeypatch.setattr(teaching_gateway, "stream_tutor_reply", should_not_stream)
    await teaching_runs.execute(run["run_id"])
    state = await teaching_runs.get(db_session, Principal(user), run["run_id"])
    assert state["status"] == "needs_retry"
    assert state["error_code"] == "LESSON_WITHDRAWN"


async def test_retried_first_turn_replays_after_withdrawal(db_session, monkeypatch):
    user, lesson, revision_id = await seed(db_session, monkeypatch)
    body = tutor_input(revision_id)
    run = await teaching_runs.start_lesson_turn(db_session, Principal(user), lesson, body)
    revision = await db_session.get(LessonRevision, revision_id)
    revision.status = "withdrawn"
    await db_session.commit()

    # The client never saw the 202 (network failure) and retries. The retry must
    # return the original run, not 410: the receipt is the answer to "what
    # happened to my request", and it already exists.
    replay = await teaching_runs.start_lesson_turn(db_session, Principal(user), lesson, body)
    assert replay["run_id"] == run["run_id"]


async def test_archived_lesson_conversation_cannot_start_a_run(db_session, monkeypatch):
    user, lesson, revision_id = await seed(db_session, monkeypatch)
    run = await teaching_runs.start_lesson_turn(db_session, Principal(user), lesson, tutor_input(revision_id))
    conversation = await db_session.get(TutorConversation, run["conversation_id"])
    conversation.status = "archived"
    await db_session.commit()

    follow_up = SimpleNamespace(
        revision_id=revision_id,
        segment_id=SEGMENT,
        token_ids=TOKENS,
        request_id="tutor-turn-2",
        conversation_id=run["conversation_id"],
        message="再讲一遍",
    )
    with pytest.raises(AppError) as archived:
        await teaching_runs.start_lesson_turn(db_session, Principal(user), lesson, follow_up)
    assert archived.value.status_code == 409


@pytest.mark.integration
async def test_postgres_concurrent_course_saves_and_review_replay(monkeypatch):
    maker = get_async_session_maker()
    async with maker() as db:
        assert db.get_bind().dialect.name == "postgresql"
        user, lesson, revision_id = await seed(db, monkeypatch)

    async def race(action):
        gate = asyncio.Barrier(2)

        async def run():
            async with maker() as db:
                await gate.wait()
                result = await action(db)
                await db.commit()
                return result

        return await asyncio.wait_for(asyncio.gather(run(), run()), timeout=20)

    async def save(db):
        return await lesson_learning.save_source(db, user, lesson, revision_id, SEGMENT, TOKENS)

    first, second = await race(save)
    assert first == second
    word_id = first["word_id"]

    async def review(db):
        return await vocabulary_service.record_idempotent_review(db, user, word_id, 5, "same-review")

    first, second = await race(review)
    assert first == second
    async with maker() as db:
        assert (await db.get(Vocabulary, word_id)).review_count == 1
        assert await db.scalar(select(func.count(VocabularyReviewLog.id))) == 1
        assert await db.scalar(select(func.count(LessonVocabularySource.id))) == 1


@pytest.mark.integration
async def test_account_purge_removes_lesson_anchors(monkeypatch):
    """Anchors hang off a word and a conversation; only the purge can find them."""
    from app.tasks.account_tasks import _purge_user

    maker = get_async_session_maker()
    async with maker() as db:
        user, lesson, revision_id = await seed(db, monkeypatch)
    async with maker() as db:
        saved = await lesson_learning.save_source(db, user, lesson, revision_id, SEGMENT, TOKENS)
        await db.commit()
        word_id = saved["word_id"]
    async with maker() as db:
        user_row = await db.get(User, user)
        assert user_row is not None
        await _purge_user(db, user_row)
    async with maker() as db:
        assert await db.get(User, user) is None
        assert await db.get(Vocabulary, word_id) is None
        assert await db.scalar(select(func.count(LessonVocabularySource.id))) == 0

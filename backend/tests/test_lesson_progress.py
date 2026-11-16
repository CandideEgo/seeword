"""Lesson progress: completion is a lesson-level fact, not a revision-level one."""

import json
from pathlib import Path

import pytest

from app.core.errors import AppError
from app.models.lesson import Lesson, LessonProgress, LessonRevision
from app.models.user import User
from app.schemas.lesson import RecordLessonActivity, SaveLessonProgress
from app.services import lesson_progress
from app.services.video_learning_material import load_video_material

PACK = Path(__file__).resolve().parents[2] / "docs" / "slcs" / "examples" / "welcome-to-wikisource.json"


async def seed(db, *, access_mode="provider_embed", revisions=2):
    pack = json.loads(PACK.read_bytes())
    pack["media"] = {
        **pack["media"],
        "access_mode": access_mode,
        "source_url": "https://youtube.com/watch?v=abcdefghijk"
        if access_mode == "provider_embed"
        else pack["media"]["source_url"],
    }
    user = User(phone="13800001291", name="Progress Learner")
    lesson = Lesson(id=pack["lesson_id"])
    db.add_all([user, lesson])
    await db.flush()
    ids = []
    for index in range(revisions):
        title = pack["title"] if index == 0 else f"{pack['title']} v{index + 1}"
        document = {**pack, "title": title}
        material = load_video_material(json.dumps(document, ensure_ascii=False).encode("utf-8"))
        revision = LessonRevision(
            lesson_id=lesson.id,
            fingerprint=material.source_fingerprint,
            fingerprint_version="slcs-pack-v1",
            title=title,
            access_mode=access_mode,
            pack=document,
            status="published",
            review={
                "uses": {
                    "site_display": {"approved": True},
                    "model_processing": {"approved": False},
                }
            },
        )
        db.add(revision)
        await db.flush()
        ids.append(revision.id)
        if index == 0:
            lesson.current_revision_id = revision.id
            await db.flush()
    await db.commit()
    return user.id, lesson.id, ids


async def complete(db, user, lesson, revision, event_id="complete-1"):
    return await lesson_progress.record_activity(
        db, user, lesson, RecordLessonActivity(revision_id=revision, event_id=event_id, event_type="complete")
    )


async def watch(db, user, lesson, revision, event_id, delta=8.0):
    return await lesson_progress.record_activity(
        db,
        user,
        lesson,
        RecordLessonActivity(revision_id=revision, event_id=event_id, event_type="watch_time", delta_s=delta),
    )


async def test_completion_survives_a_position_save_on_another_revision(db_session):
    user, lesson, (first, second) = await seed(db_session)
    assert (await complete(db_session, user, lesson, first))["completed"] is True
    await db_session.commit()

    # An old tab (or an old deep link) saving its position on the other revision
    # must not resurrect "not finished".
    result = await lesson_progress.save_progress(
        db_session, user, lesson, SaveLessonProgress(revision_id=second, position_ms=400)
    )
    await db_session.commit()
    assert result["revision_id"] == second
    assert result["position_ms"] == 400
    assert result["completed"] is True
    assert (await lesson_progress.read_progress(db_session, user, lesson))["completed"] is True


async def test_completion_while_viewing_an_older_revision_still_counts(db_session):
    user, lesson, (first, second) = await seed(db_session)
    await lesson_progress.save_progress(
        db_session, user, lesson, SaveLessonProgress(revision_id=first, position_ms=120)
    )
    await db_session.flush()

    # The learner finished the lesson while reading the pinned older revision.
    result = await complete(db_session, user, lesson, second)
    await db_session.commit()
    assert result["completed"] is True
    assert result["revision_id"] == second
    progress = await lesson_progress.read_progress(db_session, user, lesson)
    assert progress["completed"] is True
    # The resume pointer followed what was actually being watched.
    assert progress["revision_id"] == second
    # And watched time accumulates across revisions rather than resetting.
    assert progress["watch_seconds"] == 0.0


async def test_external_link_records_explicit_completion_but_no_timer(db_session):
    user, lesson, (revision,) = await seed(db_session, access_mode="external_link", revisions=1)
    with pytest.raises(AppError) as no_clock:
        await watch(db_session, user, lesson, revision, "external-clock")
    assert no_clock.value.status_code == 422
    # Marking the lesson complete is an explicit learner action: it is allowed,
    # and the bundled Wikisource reference pack is an external link.
    result = await complete(db_session, user, lesson, revision)
    await db_session.commit()
    assert result["completed"] is True


async def test_repeated_event_returns_the_same_state_and_records_once(db_session):
    user, lesson, (revision, _) = await seed(db_session)
    first = await watch(db_session, user, lesson, revision, "same-event", delta=9.0)
    second = await watch(db_session, user, lesson, revision, "same-event", delta=9.0)
    await db_session.commit()
    assert first == second
    row = await db_session.get(LessonProgress, (user, lesson), populate_existing=True)
    assert row is not None and row.watch_seconds == 9.0

    with pytest.raises(AppError) as conflict:
        await watch(db_session, user, lesson, revision, "same-event", delta=11.0)
    assert conflict.value.status_code == 409


async def test_position_beyond_the_media_duration_is_rejected(db_session):
    user, lesson, (revision, _) = await seed(db_session)
    with pytest.raises(AppError) as too_far:
        await lesson_progress.save_progress(
            db_session, user, lesson, SaveLessonProgress(revision_id=revision, position_ms=10**9)
        )
    assert too_far.value.status_code == 422


async def test_course_and_video_time_are_summed_per_local_day(db_session):
    """The study-time read model unions both tables; the week figure must not double count."""
    from datetime import UTC, datetime, timedelta
    from zoneinfo import ZoneInfo

    from app.models.behavior import BehaviorEvent
    from app.services.study_time_service import watch_seconds_by_local_day

    user, lesson, (revision, _) = await seed(db_session)
    now = datetime.now(UTC)
    db_session.add(BehaviorEvent(user_id=user, event_type="watch_time", event_payload={"delta_s": 30.0}, server_ts=now))
    await watch(db_session, user, lesson, revision, "union-1", delta=12.0)
    await db_session.commit()

    seconds = await watch_seconds_by_local_day(
        db_session,
        user,
        start=now - timedelta(hours=1),
        end=now + timedelta(hours=1),
        tz=ZoneInfo("UTC"),
    )
    assert sum(seconds.values()) == 42

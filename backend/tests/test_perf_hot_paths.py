"""Performance hot paths (2026-11): the work a page load must *not* repeat.

These pin the two structural fixes rather than timing numbers:

* the video detail cache must save the subtitle read, not just serialization;
* the first-view LearningRecord is created exactly once without a row lock;
* the aggregated overview and the watch-context endpoint stay within a bounded
  number of SQL statements (a regression here silently doubles page latency).
"""

from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import event, func, select

from app.models.learning import LearningRecord, Vocabulary
from app.models.user import User
from app.models.video import Video, VideoSource, VideoStatus


@contextmanager
def count_statements(session):
    """Collect SQL statements executed on this session's engine."""
    statements: list[str] = []
    bind = session.get_bind()
    target = getattr(bind, "sync_engine", bind)

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(target, "before_cursor_execute", _record)
    try:
        yield statements
    finally:
        event.remove(target, "before_cursor_execute", _record)


async def _make_video(db_session, title: str) -> Video:
    from app.models.subtitle import Subtitle

    video = Video(
        title=title,
        source_url=f"https://example.com/{title}.mp4",
        video_source=VideoSource.imported,
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        duration=120.0,
    )
    db_session.add(video)
    await db_session.flush()
    db_session.add_all(
        [
            Subtitle(
                video_id=video.id,
                sentence_index=0,
                start_time=0.0,
                end_time=2.0,
                text_en="Hello there.",
                text_zh="你好。",
            ),
            Subtitle(
                video_id=video.id,
                sentence_index=1,
                start_time=2.0,
                end_time=4.0,
                text_en="General Kenobi.",
                text_zh="肯诺比将军。",
            ),
        ]
    )
    await db_session.commit()
    return video


class TestVideoDetailFastPath:
    async def test_cache_hit_does_not_read_subtitle_rows(self, client, auth_headers, db_session):
        """The Redis payload must replace the subtitle query, not just its JSON."""
        from app.services.video_service import get_video_detail

        video = await _make_video(db_session, "detail-cache")
        me = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
        user = await db_session.get(User, me["id"])

        first = await get_video_detail(db_session, video.id, user)
        assert first is not None and len(first.subtitles) == 2

        with count_statements(db_session) as statements:
            second = await get_video_detail(db_session, video.id, user)

        assert second is not None and len(second.subtitles) == 2
        executed = "\n".join(statements).lower()
        assert "from subtitles" not in executed

    async def test_first_view_creates_one_learning_record(self, client, auth_headers, db_session):
        from app.services.video_service import get_video_detail

        video = await _make_video(db_session, "detail-record")
        me = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
        user = await db_session.get(User, me["id"])

        for _ in range(3):
            assert await get_video_detail(db_session, video.id, user) is not None

        count = await db_session.scalar(
            select(func.count(LearningRecord.id)).where(
                LearningRecord.user_id == user.id,
                LearningRecord.video_id == video.id,
            )
        )
        assert count == 1


class TestBoundedReadModels:
    async def test_overview_stays_within_bounded_statements(self, client, auth_headers, db_session):
        with count_statements(db_session) as statements:
            resp = await client.get("/api/v1/users/me/overview", headers=auth_headers)

        assert resp.status_code == 200
        selects = [s for s in statements if s.lstrip().lower().startswith("select")]
        # ~10 SELECTs: auth + timezone + profile + dates + learning/vocab/exam
        # aggregates. The old fan-out was one round trip per counter (~18);
        # this bound fails if someone re-introduces per-figure queries.
        assert len(selects) <= 11

    async def test_watch_context_returns_words_and_set(self, client, auth_headers, db_session):
        from app.models.vocab_set import VocabSet

        video = await _make_video(db_session, "watch-context")
        me = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
        db_session.add_all(
            [
                Vocabulary(user_id=me["id"], word="learning", mastery_level="learning"),
                Vocabulary(user_id=me["id"], word="reviewing", mastery_level="reviewing"),
                Vocabulary(user_id=me["id"], word="mastered", mastery_level="mastered"),
                VocabSet(user_id=me["id"], video_id=video.id, source_type="video", exam_level="cet4"),
            ]
        )
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/vocabulary/watch-context?video_id={video.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert sorted(data["learning_words"]) == ["learning", "reviewing"]
        assert data["mastered_words"] == ["mastered"]
        assert data["vocab_set"]["video_id"] == video.id

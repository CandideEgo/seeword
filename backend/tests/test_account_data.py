"""A08/BE-04：数据导出完整性与注销清理的可重试契约。

与 ``test_account_deletion.py`` 的分工：那边测 30 天冷静期与下载握手，这里测
**数据面**——专用账号的导出包含收藏/笔记/词汇/各类练习/媒体，且不含另一个
账号的数据；注销后目标数据与媒体清理完成，失败可重试；官方视频与财务流水
按约定保留（脱敏）。
"""

import json
import zipfile
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.behavior import BehaviorEvent
from app.models.channel import Channel
from app.models.data_export import DataExportTask
from app.models.engagement import VideoLike
from app.models.exam_test import ExamAnswer, ExamSession
from app.models.favorite import UserFavorite, UserNote
from app.models.feedback import Feedback
from app.models.learning import LearningRecord, Vocabulary
from app.models.learning_plan import LearningEvent, UserLearningProfile
from app.models.listening import ListeningSession
from app.models.media_cleanup import MediaCleanupTask
from app.models.milestone import MasterySnapshot, UserMilestone
from app.models.notification import Notification
from app.models.preferences import UserPreferences
from app.models.study_session import StudySession, StudySessionItem
from app.models.subtitle import Subtitle
from app.models.user import User
from app.models.user_content import ChannelSubscription, SentenceFavorite
from app.models.video import Video
from app.models.vocab_set import VocabSet, VocabSetWord
from app.services import account_data
from app.tasks.account_tasks import _purge_due, build_user_export
from tests.conftest import TestSessionLocal


@pytest.fixture
def media_tmp(tmp_path, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "local_media_path", str(tmp_path))
    return tmp_path


async def _seed_all(user_id: str, marker: str) -> dict:
    """One row in every section the export advertises, tagged with ``marker``."""
    now = datetime.now(UTC)
    ids: dict[str, str] = {}
    async with TestSessionLocal() as db:
        video = Video(
            user_id=user_id,
            title=f"owned-{marker}",
            source_url=f"https://example.com/{marker}.mp4",
            is_official=False,
            video_url_720p=f"/media/{marker}_720p.mp4",
        )
        official = Video(
            user_id=user_id,
            title=f"official-{marker}",
            source_url=f"https://example.com/{marker}-official.mp4",
            is_official=True,
            is_published=True,
            video_url_720p=f"/media/official_{marker}.mp4",
        )
        db.add_all([video, official])
        await db.flush()
        ids["video"] = video.id
        ids["official_video"] = official.id

        subtitle = Subtitle(video_id=video.id, sentence_index=0, start_time=0, end_time=1, text_en=f"line-{marker}")
        channel = Channel(name=f"channel-{marker}", slug=f"channel-{marker}")
        db.add_all([subtitle, channel])
        await db.flush()
        ids["subtitle"] = subtitle.id
        ids["channel"] = channel.id

        vocab = Vocabulary(user_id=user_id, word=f"word{marker}", translation="n. 标记")
        db.add(vocab)
        await db.flush()
        ids["vocabulary"] = vocab.id

        db.add_all(
            [
                LearningRecord(user_id=user_id, video_id=video.id, words_learned=3),
                LearningEvent(user_id=user_id, event_type="learned_words", event_value=3, event_date=date.today()),
                UserLearningProfile(user_id=user_id),
                UserPreferences(user_id=user_id, target_exam="cet4"),
                UserFavorite(user_id=user_id, video_id=video.id),
                UserNote(user_id=user_id, video_id=video.id, content=f"note-{marker}"),
                SentenceFavorite(user_id=user_id, subtitle_id=subtitle.id),
                ChannelSubscription(user_id=user_id, channel_id=channel.id),
                VideoLike(user_id=user_id, video_id=video.id),
                ListeningSession(user_id=user_id, video_id=video.id, title=f"listen-{marker}"),
                Notification(user_id=user_id, type="system", title=f"notify-{marker}"),
                Feedback(user_id=user_id, content=f"feedback-{marker}"),
                MasterySnapshot(user_id=user_id, snapshot_date=date.today(), mastery_json={"cet4": {"mastered": 1}}),
                UserMilestone(user_id=user_id, milestone_type=f"first-{marker}"),
                BehaviorEvent(user_id=user_id, event_type="watch_time", event_payload={"marker": marker}),
            ]
        )
        await db.flush()

        study = StudySession(user_id=user_id, local_date=date.today(), target_count=2)
        vocab_set = VocabSet(user_id=user_id, video_id=video.id, exam_level="cet4")
        db.add_all([study, vocab_set])
        await db.flush()
        db.add_all(
            [
                StudySessionItem(session_id=study.id, vocabulary_id=vocab.id, sort_order=1),
                VocabSetWord(set_id=vocab_set.id, vocabulary_id=vocab.id, position=1),
            ]
        )

        exam = ExamSession(
            user_id=user_id,
            mode="paper_exam",
            question_count=1,
            started_at=now,
            submitted_at=now,
            score=1.0,
        )
        db.add(exam)
        await db.flush()
        db.add(
            ExamAnswer(
                session_id=exam.id,
                question={"stem": f"exam-{marker}", "answer": "A"},
                user_answer="A",
                correct=True,
                answered_at=now,
            )
        )
        await db.commit()

        ids["study_session"] = study.id
        ids["vocab_set"] = vocab_set.id
        ids["exam_session"] = exam.id
    return ids


async def _seed_user(phone: str, name: str) -> str:
    async with TestSessionLocal() as db:
        user = User(phone=phone, name=name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user.id


def _zip_payload(zip_path) -> dict[str, str]:
    with zipfile.ZipFile(zip_path) as zf:
        return {name: zf.read(name).decode("utf-8", "replace") for name in zf.namelist() if name.endswith(".json")}


async def test_export_contains_every_section_and_no_other_user(media_tmp):
    alpha_id = await _seed_user("13800001001", "Alpha")
    bravo_id = await _seed_user("13800001002", "Bravo")
    alpha = await _seed_all(alpha_id, "alpha")
    await _seed_all(bravo_id, "bravo")

    # Media: avatar + uploaded video + historical shadowing audio for Alpha;
    # a second avatar for Bravo.
    (media_tmp / "avatars").mkdir(parents=True)
    (media_tmp / "avatars" / "alpha.png").write_bytes(b"alpha-avatar")
    (media_tmp / "avatars" / "bravo.png").write_bytes(b"bravo-avatar")
    (media_tmp / "shadowing" / alpha_id).mkdir(parents=True)
    (media_tmp / "shadowing" / alpha_id / "rec.webm").write_bytes(b"alpha-recording")
    (media_tmp / "alpha_720p.mp4").write_bytes(b"alpha-video")
    (media_tmp / f"{alpha['video']}_raw.mp4").write_bytes(b"alpha-raw")

    async with TestSessionLocal() as db:
        user = await db.get(User, alpha_id)
        assert user is not None
        user.avatar_url = "/media/avatars/alpha.png"
        task = DataExportTask(user_id=alpha_id, status="pending")
        db.add(task)
        await db.commit()
        task_id = task.id

    assert build_user_export(task_id)["status"] == "ready"

    async with TestSessionLocal() as db:
        task = await db.get(DataExportTask, task_id)
        assert task is not None and task.file_path
        zip_path = media_tmp / task.file_path

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

    expected_sections = {
        "profile",
        "preferences",
        "learning_profile",
        "vocabulary",
        "learning_records",
        "learning_events",
        "vocab_sets",
        "study_sessions",
        "favorites",
        "notes",
        "sentence_favorites",
        "channel_subscriptions",
        "video_likes",
        "listening_sessions",
        "exam_sessions",
        "videos",
        "notifications",
        "feedbacks",
        "mastery_snapshots",
        "user_milestones",
        "behavior_events",
    }
    for section in expected_sections:
        assert f"{section}.json" in names, section
    assert "media/avatar/alpha.png" in names
    assert "media/videos/alpha_720p.mp4" in names
    assert f"media/videos/{alpha['video']}_raw.mp4" in names
    assert "media/shadowing/rec.webm" in names

    payloads = _zip_payload(zip_path)
    assert json.loads(payloads["profile.json"])["phone"] == "13800001001"
    assert json.loads(payloads["notes.json"])[0]["content"] == "note-alpha"
    assert json.loads(payloads["favorites.json"])[0]["video_id"] == alpha["video"]
    assert json.loads(payloads["vocab_sets.json"])[0]["words"][0]["vocabulary_id"]
    assert json.loads(payloads["study_sessions.json"])[0]["items"][0]["sort_order"] == 1
    assert json.loads(payloads["exam_sessions.json"])[0]["answers"][0]["user_answer"] == "A"
    combined = "\n".join(payloads.values())
    assert "bravo" not in combined  # never another user's rows
    assert str(bravo_id) not in combined


async def test_export_children_do_not_cross_users(media_tmp):
    alpha_id = await _seed_user("13800001003", "Alpha2")
    bravo_id = await _seed_user("13800001004", "Bravo2")
    await _seed_all(alpha_id, "alpha2")
    bravo = await _seed_all(bravo_id, "bravo2")

    async with TestSessionLocal() as db:
        task = DataExportTask(user_id=alpha_id, status="pending")
        db.add(task)
        await db.commit()
        task_id = task.id
    build_user_export(task_id)

    async with TestSessionLocal() as db:
        task = await db.get(DataExportTask, task_id)
        zip_path = media_tmp / task.file_path

    payloads = _zip_payload(zip_path)
    assert bravo["exam_session"] not in payloads["exam_sessions.json"]
    assert bravo["study_session"] not in payloads["study_sessions.json"]
    assert bravo["vocab_set"] not in payloads["vocab_sets.json"]


async def test_purge_removes_user_data_and_media_but_keeps_shared_records(media_tmp):
    alpha_id = await _seed_user("13800001005", "PurgeAlpha")
    bravo_id = await _seed_user("13800001006", "PurgeBravo")
    alpha = await _seed_all(alpha_id, "purgealpha")
    await _seed_all(bravo_id, "purgebravo")

    (media_tmp / "avatars").mkdir(parents=True)
    (media_tmp / "avatars" / "purgealpha.png").write_bytes(b"a")
    (media_tmp / "avatars" / "purgebravo.png").write_bytes(b"b")
    (media_tmp / "shadowing" / alpha_id).mkdir(parents=True)
    (media_tmp / "shadowing" / alpha_id / "rec.webm").write_bytes(b"rec")
    (media_tmp / "purgealpha_720p.mp4").write_bytes(b"video")
    (media_tmp / "official_purgealpha_720p.mp4").write_bytes(b"official")
    (media_tmp / f"{alpha['video']}_raw.mp4").write_bytes(b"raw")
    (media_tmp / "exports" / alpha_id).mkdir(parents=True)
    (media_tmp / "exports" / alpha_id / "old.zip").write_bytes(b"zip")

    async with TestSessionLocal() as db:
        user = await db.get(User, alpha_id)
        bravo = await db.get(User, bravo_id)
        assert user is not None and bravo is not None
        user.avatar_url = "/media/avatars/purgealpha.png"
        bravo.avatar_url = "/media/avatars/purgebravo.png"
        user.deletion_scheduled_at = datetime.now(UTC) - timedelta(minutes=1)
        user.deletion_requested_at = datetime.now(UTC) - timedelta(days=31)
        db.add(DataExportTask(user_id=alpha_id, status="ready", file_path=f"exports/{alpha_id}/old.zip"))
        await db.commit()

    assert await _purge_due(now=datetime.now(UTC)) == 1

    async with TestSessionLocal() as db:
        assert await db.get(User, alpha_id) is None
        assert await db.get(User, bravo_id) is not None
        for model, column in [
            (Vocabulary, Vocabulary.user_id),
            (LearningRecord, LearningRecord.user_id),
            (LearningEvent, LearningEvent.user_id),
            (UserLearningProfile, UserLearningProfile.user_id),
            (UserPreferences, UserPreferences.user_id),
            (UserFavorite, UserFavorite.user_id),
            (UserNote, UserNote.user_id),
            (SentenceFavorite, SentenceFavorite.user_id),
            (ChannelSubscription, ChannelSubscription.user_id),
            (VideoLike, VideoLike.user_id),
            (ListeningSession, ListeningSession.user_id),
            (ExamSession, ExamSession.user_id),
            (Notification, Notification.user_id),
            (Feedback, Feedback.user_id),
            (MasterySnapshot, MasterySnapshot.user_id),
            (UserMilestone, UserMilestone.user_id),
            (StudySession, StudySession.user_id),
            (VocabSet, VocabSet.user_id),
        ]:
            assert (await db.execute(select(model).where(column == alpha_id))).scalars().all() == [], model.__name__
        assert (await db.get(Video, alpha["video"])) is None
        official = await db.get(Video, alpha["official_video"])
        assert official is not None and official.user_id is None
        assert (await db.execute(select(Video).where(Video.user_id == bravo_id))).scalars().all() != []

        events = (await db.execute(select(BehaviorEvent).where(BehaviorEvent.user_id.is_(None)))).scalars().all()
        assert any(event.event_payload == {"marker": "purgealpha"} for event in events)

        cleanup = (await db.execute(select(MediaCleanupTask))).scalars().all()
        assert cleanup and all(row.status == "done" for row in cleanup)

    assert not (media_tmp / "avatars" / "purgealpha.png").exists()
    assert (media_tmp / "avatars" / "purgebravo.png").exists()
    assert not (media_tmp / "shadowing" / alpha_id).exists()
    assert not (media_tmp / "purgealpha_720p.mp4").exists()
    # Official video media belongs to the platform and survives the uploader.
    assert (media_tmp / "official_purgealpha_720p.mp4").exists()
    assert not (media_tmp / f"{alpha['video']}_raw.mp4").exists()
    assert not (media_tmp / "exports" / alpha_id).exists()


async def test_media_cleanup_retries_until_the_path_is_gone(media_tmp):
    (media_tmp / "avatars").mkdir(parents=True)
    blocked = media_tmp / "avatars" / "locked.png"
    blocked.mkdir()  # a directory where the queue expects a file → unlink fails

    async with TestSessionLocal() as db:
        await account_data.enqueue_media_cleanup(db, "cleanup-user", ["avatars/locked.png"], [])
        await db.commit()
        first = await account_data.process_media_cleanup(db, now=datetime.now(UTC))
        assert first["failed"] == 1
        row = (await db.execute(select(MediaCleanupTask))).scalar_one()
        assert row.status == "pending" and row.attempts == 1 and row.next_attempt_at is not None

        # Still failing: the retry respects the backoff window and records it.
        retry_at = row.next_attempt_at
        second = await account_data.process_media_cleanup(db, now=retry_at)
        assert second["failed"] == 1
        await db.refresh(row)
        assert row.attempts == 2

        blocked.rmdir()
        third = await account_data.process_media_cleanup(db, now=datetime.now(UTC) + timedelta(hours=2))
        assert third["done"] == 1
        await db.refresh(row)
        assert row.status == "done" and row.last_error is None

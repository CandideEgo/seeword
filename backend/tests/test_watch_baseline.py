"""Watch progress, source integrity and retired feature contracts."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.models.learning import LearningRecord, Vocabulary
from app.models.notification import Notification
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoSource, VideoStatus
from app.services.milestone_service import check_and_award
from app.services.retired_features import RETIRED_NOTIFICATION_TYPES
from app.tasks.celery_app import celery_app
from tests.conftest import TestSessionLocal


async def seed_source():
    async with TestSessionLocal() as db:
        video = Video(
            title="Watch baseline",
            source_url="https://example.com/watch.mp4",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            is_official=True,
            duration=20,
        )
        other = Video(
            title="Other",
            source_url="https://example.com/other.mp4",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            is_official=True,
            duration=20,
        )
        db.add_all([video, other])
        await db.flush()
        a = Subtitle(video_id=video.id, start_time=0, end_time=3, sentence_index=0, text_en="I walk into it.")
        b = Subtitle(video_id=video.id, start_time=10, end_time=13, sentence_index=1, text_en="Then I walk home.")
        db.add_all([a, b])
        await db.commit()
        return video.id, other.id, a.id, b.id


async def test_progress_clamped_and_does_not_claim_completion(client, auth_headers):
    video, _, _, _ = await seed_source()
    resp = await client.patch(
        "/api/v1/learning/progress", headers=auth_headers, json={"video_id": video, "position_seconds": 900}
    )
    assert resp.status_code == 200
    assert resp.json() == {"position_seconds": 20, "progress_percentage": 100}
    async with TestSessionLocal() as db:
        record = (await db.execute(select(LearningRecord).where(LearningRecord.video_id == video))).scalar_one()
        assert not record.completed


async def test_save_word_uses_clicked_source_not_first_occurrence(client, auth_headers):
    video, _, first, second = await seed_source()
    resp = await client.post(
        "/api/v1/vocabulary",
        headers=auth_headers,
        params={
            "word": "walk",
            "video_id": video,
            "subtitle_id": second,
            "context_sentence": "I walk into it.",
        },
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subtitle_id"] == second != first
    assert resp.json()["context_sentence"] == "Then I walk home."


@pytest.mark.parametrize("endpoint", ["/api/v1/vocabulary", "/api/v1/words/gloss/enrich"])
async def test_reject_mismatched_source_without_writing(client, auth_headers, endpoint):
    _, other, _, second = await seed_source()
    resp = await client.request(
        "POST" if endpoint.endswith("vocabulary") else "GET",
        endpoint,
        headers=auth_headers,
        params={"word": "walk", "video_id": other, "subtitle_id": second},
    )
    assert resp.status_code == 409, resp.text
    async with TestSessionLocal() as db:
        assert (await db.scalar(select(func.count()).select_from(Vocabulary))) == 0


@pytest.mark.parametrize("scope,source", [("video", "video:test"), ("general", "global")])
async def test_gloss_labels_hint_scope_without_new_ai(client, auth_headers, monkeypatch, scope, source):
    async def cached(*args, **kwargs):
        return {"source": source, "contextual_note": "A usage hint", "pitfalls": None, "knowledge": None}

    monkeypatch.setattr("app.services.word_notes.get_best_note", cached)
    resp = await client.get("/api/v1/words/gloss/enrich", headers=auth_headers, params={"word": "walk"})
    assert resp.status_code == 200
    assert resp.json()["note_scope"] == scope


@pytest.mark.parametrize(
    "method,path",
    [
        ("POST", "/api/v1/shadowing/attempts"),
        ("GET", "/api/v1/shadowing/attempts"),
        ("PATCH", "/api/v1/shadowing/attempts/old"),
        ("DELETE", "/api/v1/shadowing/attempts/old"),
        ("GET", "/api/v1/shadowing/stats"),
        ("POST", "/media/shadowing-audio"),
        ("GET", "/api/v1/learning/stats/heatmap"),
        ("GET", "/api/v1/plan/milestones"),
        ("GET", "/api/v1/learning/weekly-reports"),
        ("GET", "/api/v1/learning/weekly-reports/latest"),
        ("GET", "/api/v1/videos/old/shadowing-sentences"),
    ],
)
async def test_retired_routes_auth_and_gone(client, auth_headers, method, path):
    assert (await client.request(method, path)).status_code == 401
    resp = await client.request(method, path, headers=auth_headers)
    assert resp.status_code == 410, resp.text
    assert resp.json()["code"] == "FEATURE_RETIRED"


async def test_hidden_notifications_and_unread_count_use_same_filter(client, auth_headers):
    user = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
    async with TestSessionLocal() as db:
        db.add_all(
            [
                Notification(user_id=user["id"], type=t, title="Old feature", is_read=False)
                for t in RETIRED_NOTIFICATION_TYPES
            ]
        )
        db.add(Notification(user_id=user["id"], type="system", title="Account notice", is_read=False))
        await db.commit()
    listing = await client.get("/api/v1/notifications", headers=auth_headers)
    count = await client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert listing.json()["total"] == count.json()["count"] == 1
    assert listing.json()["items"][0]["title"] == "Account notice"


async def test_retired_preferences_cannot_be_reenabled(client, auth_headers):
    resp = await client.put(
        "/api/v1/notifications/preferences",
        headers=auth_headers,
        json={
            "weekly_report": True,
            "streak_reminder": True,
            "vocabulary_reminder": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["weekly_report"] is False
    assert resp.json()["streak_reminder"] is False
    assert resp.json()["vocabulary_reminder"] is True
    assert (await client.get("/api/v1/notifications/preferences", headers=auth_headers)).json()[
        "weekly_report"
    ] is False


async def test_retired_producers_stay_retired():
    """The weekly-report/redeem producers are gone; only compatibility shells remain."""
    assert "generate-weekly-reports" not in celery_app.conf.beat_schedule
    assert "expire-unused-redeem-codes" not in celery_app.conf.beat_schedule
    async with TestSessionLocal() as db:
        assert await check_and_award(db, "unused-user") == []


async def test_old_worker_push_cannot_reintroduce_retired_badge():
    from app.api.v1.notifications import ConnectionManager

    manager = ConnectionManager()
    socket = AsyncMock()
    await manager.connect("user", socket)
    for retired in RETIRED_NOTIFICATION_TYPES:
        await manager.send_to_user("user", {"type": "notification", "notification": {"type": retired}})
    socket.send_json.assert_not_awaited()
    account_notice = {"type": "notification", "notification": {"type": "system"}}
    await manager.send_to_user("user", account_notice)
    socket.send_json.assert_awaited_once_with(account_notice)

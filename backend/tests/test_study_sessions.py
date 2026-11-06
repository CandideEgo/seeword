"""Tests for the persisted training round (study_sessions / study_session_items).

Covers DEC-053: the daily quota drives the round's size, an unfinished round is
resumed instead of restarted, 加练 takes different words and grows today's
total, and finishing sweeps the user's expired rounds.
"""

from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient

from app.models.learning import Vocabulary
from app.models.study_session import StudySession, StudySessionItem
from app.services.local_time import get_user_local_date
from tests.conftest import TestSessionLocal


async def _get_user_id(client: AsyncClient, auth_headers: dict) -> str:
    me = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
    return me["id"]


async def _seed_new_words(user_id: str, count: int) -> None:
    """Seed ``count`` words that are eligible for a round (mastery_level = new)."""
    async with TestSessionLocal() as db:
        for i in range(count):
            db.add(
                Vocabulary(
                    user_id=user_id,
                    word=f"word{i:03d}",
                    mastery_level="new",
                    created_at=datetime.now(UTC) - timedelta(minutes=count - i),
                )
            )
        await db.commit()


async def _start(client: AsyncClient, auth_headers: dict, kind: str = "daily") -> dict:
    resp = await client.post(
        "/api/v1/vocabulary/sessions",
        json={"kind": kind},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestRoundLifecycle:
    async def test_requires_auth(self, client: AsyncClient):
        assert (await client.get("/api/v1/vocabulary/sessions/current")).status_code == 401
        assert (await client.post("/api/v1/vocabulary/sessions", json={})).status_code == 401
        assert (await client.get("/api/v1/vocabulary/preferences")).status_code == 401

    async def test_no_active_round_reads_as_null(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/vocabulary/sessions/current", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["session"] is None
        assert resp.json()["today"] == {"words_learned": 0, "rounds": 0}

    async def test_round_size_follows_the_daily_quota(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 60)

        # Default quota is 10 new words.
        first = await _start(client, auth_headers)
        assert first["session"]["target_count"] == 10
        assert len(first["session"]["items"]) == 10
        assert first["session"]["kind"] == "daily"

    async def test_quota_change_resizes_the_next_round(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 60)

        put = await client.put(
            "/api/v1/vocabulary/preferences",
            json={"daily_new_target": 50},
            headers=auth_headers,
        )
        assert put.status_code == 200
        assert put.json()["daily_new_target"] == 50
        # The other field is untouched by a partial update.
        assert put.json()["daily_review_target"] == 20

        started = await _start(client, auth_headers)
        assert started["session"]["target_count"] == 50
        assert len(started["session"]["items"]) == 50

    async def test_preferences_reject_out_of_range(self, client: AsyncClient, auth_headers: dict):
        for bad in (4, 101):
            resp = await client.put(
                "/api/v1/vocabulary/preferences",
                json={"daily_new_target": bad},
                headers=auth_headers,
            )
            assert resp.status_code == 422, resp.text

    async def test_daily_session_queue_follows_the_quota(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 60)

        resp = await client.get("/api/v1/vocabulary/daily-session", headers=auth_headers)
        data = resp.json()
        assert len(data["new_words"]) == 10
        assert data["preferences"]["daily_new_target"] == 10
        assert data["preferences"]["quota_min"] == 5
        assert data["preferences"]["quota_max"] == 100

        await client.put(
            "/api/v1/vocabulary/preferences",
            json={"daily_new_target": 30},
            headers=auth_headers,
        )
        resp = await client.get("/api/v1/vocabulary/daily-session", headers=auth_headers)
        assert len(resp.json()["new_words"]) == 30

    async def test_explicit_counts_still_override_the_quota(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 10)

        resp = await client.get(
            "/api/v1/vocabulary/daily-session?new_count=3&review_count=4",
            headers=auth_headers,
        )
        assert len(resp.json()["new_words"]) == 3

    async def test_empty_pool_returns_no_round(self, client: AsyncClient, auth_headers: dict):
        started = await _start(client, auth_headers)
        assert started["session"] is None
        assert started["today"] == {"words_learned": 0, "rounds": 0}


class TestRoundResume:
    async def test_starting_twice_resumes_the_same_round(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)

        first = await _start(client, auth_headers)
        second = await _start(client, auth_headers)

        assert first["session"]["id"] == second["session"]["id"]
        assert len(second["session"]["items"]) == 10

        async with TestSessionLocal() as db:
            sessions = (await db.execute(StudySession.__table__.select())).all()
        assert len(sessions) == 1

    async def test_current_returns_the_unfinished_round_with_progress(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]
        first_word = started["session"]["items"][0]["vocabulary_id"]

        await client.post(
            f"/api/v1/vocabulary/sessions/{session_id}/answer",
            json={"vocabulary_id": first_word, "correct": True},
            headers=auth_headers,
        )

        resumed = (await client.get("/api/v1/vocabulary/sessions/current", headers=auth_headers)).json()
        assert resumed["session"]["id"] == session_id
        assert resumed["session"]["done_count"] == 1
        # Every word is still there in round order — progress continues, it does
        # not restart.
        assert len(resumed["session"]["items"]) == 10
        assert [i["sort_order"] for i in resumed["session"]["items"]] == list(range(10))
        answered = [i for i in resumed["session"]["items"] if i["status"] != "pending"]
        assert [i["vocabulary_id"] for i in answered] == [first_word]
        assert answered[0]["correct_streak"] == 1

    async def test_a_round_from_a_previous_day_is_not_resumed(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)

        # Backdate the round: 今日训练 is a per-day dose keyed on the user's local
        # date. Anchor with the same helper the service uses (BUG-16 / DEC-079
        # give it one basis, default Asia/Shanghai) — a host-local ``date.today()``
        # or a hardcoded UTC date drifts from it by a day around local midnight.
        async with TestSessionLocal() as db:
            session = (
                await db.execute(StudySession.__table__.select().where(StudySession.id == started["session"]["id"]))
            ).one()
            assert session.status == "active"
            yesterday = (await get_user_local_date(db, user_id)) - timedelta(days=1)
            await db.execute(
                StudySession.__table__.update()
                .where(StudySession.id == started["session"]["id"])
                .values(local_date=yesterday)
            )
            await db.commit()

        assert (await client.get("/api/v1/vocabulary/sessions/current", headers=auth_headers)).json()["session"] is None

        fresh = await _start(client, auth_headers)
        assert fresh["session"]["id"] != started["session"]["id"]

        async with TestSessionLocal() as db:
            stale = (
                await db.execute(StudySession.__table__.select().where(StudySession.id == started["session"]["id"]))
            ).one()
        assert stale.status == "abandoned"


class TestAnswers:
    async def test_correct_answer_updates_item_and_word(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]
        word_id = started["session"]["items"][0]["vocabulary_id"]

        resp = await client.post(
            f"/api/v1/vocabulary/sessions/{session_id}/answer",
            json={"vocabulary_id": word_id, "correct": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["item"]["correct_streak"] == 1
        assert body["item"]["wrong_in_round"] is False
        assert body["item"]["status"] == "learning"
        assert body["done_count"] == 1
        assert body["correct_count"] == 1
        assert body["today"]["words_learned"] == 1

        async with TestSessionLocal() as db:
            vocab = (await db.execute(Vocabulary.__table__.select().where(Vocabulary.id == word_id))).one()
        assert vocab.review_count == 1
        assert vocab.mastery_level == "learning"
        assert vocab.wrong_count == 0

    async def test_wrong_answer_records_the_wrong_count(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]
        word_id = started["session"]["items"][0]["vocabulary_id"]

        body = (
            await client.post(
                f"/api/v1/vocabulary/sessions/{session_id}/answer",
                json={"vocabulary_id": word_id, "correct": False},
                headers=auth_headers,
            )
        ).json()
        assert body["item"]["correct_streak"] == 0
        assert body["item"]["wrong_in_round"] is True
        assert body["correct_count"] == 0

        async with TestSessionLocal() as db:
            vocab = (await db.execute(Vocabulary.__table__.select().where(Vocabulary.id == word_id))).one()
        assert vocab.wrong_count == 1
        assert vocab.last_wrong_at is not None

    async def test_repeated_answers_update_one_row(self, client: AsyncClient, auth_headers: dict):
        """每词一行：反复作答是 UPDATE，不是追加。"""
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]
        word_id = started["session"]["items"][0]["vocabulary_id"]

        for correct in (True, True):
            body = (
                await client.post(
                    f"/api/v1/vocabulary/sessions/{session_id}/answer",
                    json={"vocabulary_id": word_id, "correct": correct},
                    headers=auth_headers,
                )
            ).json()

        assert body["item"]["correct_streak"] == 2
        assert body["item"]["status"] == "graduated"
        assert body["graduated"] is True
        # done_count counts words, not answers.
        assert body["done_count"] == 1
        assert body["correct_count"] == 2

        async with TestSessionLocal() as db:
            rows = (
                await db.execute(StudySessionItem.__table__.select().where(StudySessionItem.session_id == session_id))
            ).all()
        assert len(rows) == 10

    async def test_wrong_resets_a_streak(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]
        word_id = started["session"]["items"][0]["vocabulary_id"]

        for correct in (True, False, True):
            body = (
                await client.post(
                    f"/api/v1/vocabulary/sessions/{session_id}/answer",
                    json={"vocabulary_id": word_id, "correct": correct},
                    headers=auth_headers,
                )
            ).json()
        # 对 → 错 → 对 does not graduate.
        assert body["item"]["correct_streak"] == 1
        assert body["item"]["status"] == "learning"
        assert body["item"]["wrong_in_round"] is True

    async def test_unknown_round_or_word_is_404(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]

        missing_round = await client.post(
            "/api/v1/vocabulary/sessions/does-not-exist/answer",
            json={"vocabulary_id": started["session"]["items"][0]["vocabulary_id"], "correct": True},
            headers=auth_headers,
        )
        assert missing_round.status_code == 404

        outsider = await client.post(
            f"/api/v1/vocabulary/sessions/{session_id}/answer",
            json={"vocabulary_id": "not-in-this-round", "correct": True},
            headers=auth_headers,
        )
        assert outsider.status_code == 404

    async def test_another_users_round_is_404(self, client: AsyncClient, auth_headers: dict):
        from app.core.security import create_token, hash_password
        from app.models.user import RoleType, User

        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)

        async with TestSessionLocal() as db:
            intruder = User(
                phone="13700137000",
                hashed_password=hash_password("Testpass123!"),
                name="Intruder",
                role=RoleType.user,
            )
            db.add(intruder)
            await db.commit()
            await db.refresh(intruder)
            intruder_headers = {"Authorization": f"Bearer {create_token(intruder.id)}"}

        resp = await client.post(
            f"/api/v1/vocabulary/sessions/{started['session']['id']}/answer",
            json={"vocabulary_id": started["session"]["items"][0]["vocabulary_id"], "correct": True},
            headers=intruder_headers,
        )
        assert resp.status_code == 404

    async def test_answers_after_finish_are_rejected(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        session_id = started["session"]["id"]

        await client.post(f"/api/v1/vocabulary/sessions/{session_id}/finish", headers=auth_headers)
        resp = await client.post(
            f"/api/v1/vocabulary/sessions/{session_id}/answer",
            json={"vocabulary_id": started["session"]["items"][0]["vocabulary_id"], "correct": True},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestExtraRound:
    async def test_extra_round_takes_different_words_and_grows_today(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)

        daily = await _start(client, auth_headers)
        daily_words = {i["vocabulary_id"] for i in daily["session"]["items"]}
        for item in daily["session"]["items"]:
            await client.post(
                f"/api/v1/vocabulary/sessions/{daily['session']['id']}/answer",
                json={"vocabulary_id": item["vocabulary_id"], "correct": True},
                headers=auth_headers,
            )

        finished = await client.post(
            f"/api/v1/vocabulary/sessions/{daily['session']['id']}/finish",
            headers=auth_headers,
        )
        assert finished.status_code == 200
        assert finished.json()["session"]["status"] == "finished"
        assert finished.json()["today"] == {"words_learned": 10, "rounds": 1}

        extra = await _start(client, auth_headers, kind="extra")
        extra_words = {i["vocabulary_id"] for i in extra["session"]["items"]}

        assert extra["session"]["kind"] == "extra"
        assert extra["session"]["id"] != daily["session"]["id"]
        assert extra["session"]["target_count"] == 10
        assert extra_words.isdisjoint(daily_words)
        assert extra["today"]["rounds"] == 2

    async def test_extra_round_keeps_the_current_round_when_unfinished(self, client: AsyncClient, auth_headers: dict):
        """加练前必须先结束当前轮；否则拿到的是当前轮本身（幂等）。"""
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        daily = await _start(client, auth_headers)

        again = await _start(client, auth_headers, kind="extra")
        assert again["session"]["id"] == daily["session"]["id"]
        assert again["session"]["kind"] == "daily"


class TestRetention:
    async def test_finishing_sweeps_rounds_older_than_the_retention_window(
        self, client: AsyncClient, auth_headers: dict
    ):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)

        async with TestSessionLocal() as db:
            old = StudySession(
                user_id=user_id,
                local_date=date.today() - timedelta(days=40),
                kind="daily",
                target_count=1,
                status="finished",
            )
            db.add(old)
            await db.flush()
            db.add(
                StudySessionItem(
                    session_id=old.id,
                    vocabulary_id="irrelevant",
                    sort_order=0,
                    status="graduated",
                )
            )
            recent = StudySession(
                user_id=user_id,
                local_date=date.today() - timedelta(days=3),
                kind="daily",
                target_count=1,
                status="finished",
            )
            db.add(recent)
            await db.flush()
            recent_id = recent.id
            old_id = old.id
            await db.commit()

        started = await _start(client, auth_headers)
        await client.post(
            f"/api/v1/vocabulary/sessions/{started['session']['id']}/finish",
            headers=auth_headers,
        )

        async with TestSessionLocal() as db:
            remaining = {row.id for row in (await db.execute(StudySession.__table__.select())).all()}
            item_rows = (await db.execute(StudySessionItem.__table__.select())).all()

        assert old_id not in remaining
        assert recent_id in remaining
        # The old round's items went with it (explicit delete — SQLite does not
        # enforce the FK cascade).
        assert all(row.session_id != old_id for row in item_rows)

    async def test_retention_does_not_touch_other_users(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)

        async with TestSessionLocal() as db:
            other = StudySession(
                user_id="someone-else",
                local_date=date.today() - timedelta(days=40),
                kind="daily",
                target_count=1,
                status="finished",
            )
            db.add(other)
            await db.commit()
            other_id = other.id

        started = await _start(client, auth_headers)
        await client.post(
            f"/api/v1/vocabulary/sessions/{started['session']['id']}/finish",
            headers=auth_headers,
        )

        async with TestSessionLocal() as db:
            remaining = {row.id for row in (await db.execute(StudySession.__table__.select())).all()}
        assert other_id in remaining


class TestTodayVisibility:
    async def test_learned_words_grow_the_profile_counter(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)

        before = (await client.get("/api/v1/plan/profile", headers=auth_headers)).json()
        assert before["today_words_learned"] == 0

        started = await _start(client, auth_headers)
        for item in started["session"]["items"][:3]:
            await client.post(
                f"/api/v1/vocabulary/sessions/{started['session']['id']}/answer",
                json={"vocabulary_id": item["vocabulary_id"], "correct": True},
                headers=auth_headers,
            )

        after = (await client.get("/api/v1/plan/profile", headers=auth_headers)).json()
        assert after["today_words_learned"] == 3

    async def test_repeat_answers_count_the_word_once(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        word_id = started["session"]["items"][0]["vocabulary_id"]

        for _ in range(2):
            await client.post(
                f"/api/v1/vocabulary/sessions/{started['session']['id']}/answer",
                json={"vocabulary_id": word_id, "correct": True},
                headers=auth_headers,
            )

        profile = (await client.get("/api/v1/plan/profile", headers=auth_headers)).json()
        assert profile["today_words_learned"] == 1

    async def test_profile_refresh_reports_the_same_counter(self, client: AsyncClient, auth_headers: dict):
        user_id = await _get_user_id(client, auth_headers)
        await _seed_new_words(user_id, 30)
        started = await _start(client, auth_headers)
        await client.post(
            f"/api/v1/vocabulary/sessions/{started['session']['id']}/answer",
            json={"vocabulary_id": started["session"]["items"][0]["vocabulary_id"], "correct": True},
            headers=auth_headers,
        )

        refreshed = (await client.post("/api/v1/plan/profile/refresh", headers=auth_headers)).json()
        assert refreshed["today_words_learned"] == 1

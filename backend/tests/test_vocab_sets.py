"""Tests for the vocab-set + quick-sieve learning loop (产品需求 §4.6).

Covers POST/GET /api/v1/vocab-sets: level-filtered collection with the cet4
fallback and idempotent re-collect, ECDICT-only enrichment (zero AI calls),
set list sorting, detail scopes, sieve resume, known/unknown mastery sync,
single learned_words LearningEvent on set closure — plus the tri-state
behavior change that mastered words no longer appear in due review queues.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update

from app.core.security import create_token, hash_password
from app.models.learning import Vocabulary
from app.models.learning_plan import LearningEvent, UserLearningProfile
from app.models.preferences import UserPreferences
from app.models.subtitle import Subtitle
from app.models.user import RoleType, User
from app.models.video import Video, VideoStatus
from app.models.vocab_set import VocabSet, VocabSetWord
from app.services import ecdict
from tests.conftest import TestSessionLocal

# Tokens -> fake ECDICT entries. Keys mirror what ecdict.lookup returns for
# exam-tagged words (see app/services/ecdict.py::_build_index); "longpos"
# exercises the >20-char pos truncation for Vocabulary.part_of_speech.
_FAKE_ENTRIES: dict[str, dict] = {
    "apple": {
        "lemma": "apple",
        "phonetic": "'æpl",
        "definition": "n. a round fruit",
        "translation": "n. 苹果",
        "pos": "n:100",
        "tags": "cet4",
        "levels": ["cet4"],
        "bnc": 0,
    },
    "apples": {
        "lemma": "apple",
        "phonetic": "'æpl",
        "definition": "n. a round fruit",
        "translation": "n. 苹果",
        "pos": "n:100",
        "tags": "cet4",
        "levels": ["cet4"],
        "bnc": 0,
    },
    "banana": {
        "lemma": "banana",
        "phonetic": "bə'nɑːnə",
        "definition": "n. an elongated yellow fruit",
        "translation": "n. 香蕉",
        "pos": "n:98",
        "tags": "cet6",
        "levels": ["cet6"],
        "bnc": 0,
    },
    "cherry": {
        "lemma": "cherry",
        "phonetic": "'tʃeri",
        "definition": "n. a small red fruit",
        "translation": "n. 樱桃",
        "pos": "n:55",
        "tags": "cet4 cet6",
        "levels": ["cet4", "cet6"],
        "bnc": 0,
    },
    "dragonfruit": {
        "lemma": "dragonfruit",
        "phonetic": "'drægənfruːt",
        "definition": "n. a tropical fruit",
        "translation": "n. 火龙果",
        "pos": "n:10",
        "tags": "cet4",
        "levels": ["cet4"],
        "bnc": 0,
    },
    "longpos": {
        "lemma": "longpos",
        "phonetic": "'lɔŋpɔs",
        "definition": "n. a word with a very long pos string",
        "translation": "n. 长词性",
        "pos": "n:1/v:2/a:3/ad:4/adv:5/conj:6/prep:7",
        "tags": "cet4",
        "levels": ["cet4"],
        "bnc": 0,
    },
}


@pytest.fixture
def ecdict_only(monkeypatch):
    """Word data comes from a fake local ECDICT — and AI must never be called.

    Both monkeypatches raise if any code path reaches for the AI service, so
    a regression that sneaks an LLM call into the collect flow fails loudly.
    """
    monkeypatch.setattr(ecdict, "lookup", lambda token: _FAKE_ENTRIES.get(token))

    def _boom(*args, **kwargs):
        raise AssertionError("AI service must not be called in the vocab-set flow")

    monkeypatch.setattr("app.services.vocabulary_service.get_ai_service", _boom)
    monkeypatch.setattr("app.services.ai_service.get_ai_service", _boom)


async def _get_user_id(client: AsyncClient, auth_headers: dict) -> str:
    me = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
    return me["id"]


async def _seed_video(
    subtitles: list[dict],
    *,
    title: str = "Vocab Set Video",
    thumbnail_url: str = "https://img.example/thumb.jpg",
) -> str:
    """Create a video with subtitles whose word_levels are the given dicts."""
    async with TestSessionLocal() as db:
        video = Video(
            title=title,
            source_url=f"https://www.youtube.com/watch?v=vocabset_{title}",
            video_source="imported",
            status=VideoStatus.ready,
            is_official=True,
            is_published=True,
            thumbnail_url=thumbnail_url,
        )
        db.add(video)
        await db.flush()
        for i, word_levels in enumerate(subtitles):
            db.add(
                Subtitle(
                    video_id=video.id,
                    start_time=float(i * 5),
                    end_time=float(i * 5 + 4),
                    text_en=" ".join(word_levels),
                    sentence_index=i,
                    word_levels=word_levels,
                )
            )
        await db.commit()
        return video.id


async def _seed_vocab(user_id: str, rows: list[Vocabulary]) -> None:
    async with TestSessionLocal() as db:
        for row in rows:
            db.add(row)
        await db.commit()


async def _other_auth_headers() -> dict:
    async with TestSessionLocal() as db:
        user = User(
            phone="13800138999",
            hashed_password=hash_password("Otherpass1!"),
            name="Other User",
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"Authorization": f"Bearer {create_token(user.id)}"}


async def _collect(client: AsyncClient, auth_headers: dict, video_id: str, exam_level: str | None = None):
    body: dict = {"video_id": video_id}
    if exam_level is not None:
        body["exam_level"] = exam_level
    return await client.post("/api/v1/vocab-sets", json=body, headers=auth_headers)


async def _set_last_activity(set_id: str, when: datetime) -> None:
    async with TestSessionLocal() as db:
        await db.execute(update(VocabSet).where(VocabSet.id == set_id).values(last_activity_at=when))
        await db.commit()


class TestCollectSet:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/vocab-sets", json={"video_id": "nope"})
        assert resp.status_code == 401

    async def test_collect_filters_by_level_and_first_appearance_order(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video(
            [
                {"apple": ["cet4"], "banana": ["cet6"], "apples": ["cet4"]},
                {"cherry": ["cet4", "cet6"]},
                {"banana": ["cet6"]},  # repeat — deduped
            ]
        )

        resp = await _collect(client, auth_headers, video_id, "cet4")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_level"] == "cet4"
        assert data["total"] == 3
        assert data["added"] == 3
        assert data["existed"] is False
        assert data["message"] == "已按四级筛选，3 个单词加入词汇本"

        detail = (await client.get(f"/api/v1/vocab-sets/{data['id']}", headers=auth_headers)).json()
        # First-appearance order across ordered subtitles; banana is cet6-only.
        assert [w["word"] for w in detail["words"]] == ["apple", "apples", "cherry"]
        assert [w["position"] for w in detail["words"]] == [1, 2, 3]

        # A different level collects its own set from the same video.
        resp6 = await _collect(client, auth_headers, video_id, "cet6")
        assert resp6.status_code == 200
        detail6 = (await client.get(f"/api/v1/vocab-sets/{resp6.json()['id']}", headers=auth_headers)).json()
        assert [w["word"] for w in detail6["words"]] == ["banana", "cherry"]

    async def test_collect_writes_subtitle_id_and_detail_exposes_start_time(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        """词→句链路 (S7a): new vocab rows carry the first-appearance subtitle,
        and the set detail exposes subtitle_id + start_time for the deep link."""
        video_id = await _seed_video(
            [
                {"apple": ["cet4"]},
                {"cherry": ["cet4"]},
                {"apple": ["cet4"]},  # repeat — first appearance wins
            ]
        )

        resp = await _collect(client, auth_headers, video_id, "cet4")
        assert resp.status_code == 200
        detail = (await client.get(f"/api/v1/vocab-sets/{resp.json()['id']}", headers=auth_headers)).json()

        by_word = {w["word"]: w for w in detail["words"]}
        # apple first appears in subtitle #0 (start 0.0), cherry in #1 (start 5.0);
        # the repeat in subtitle #2 must not move apple's source sentence.
        assert by_word["apple"]["subtitle_id"] is not None
        assert by_word["apple"]["start_time"] == 0.0
        assert by_word["cherry"]["subtitle_id"] is not None
        assert by_word["cherry"]["start_time"] == 5.0
        assert by_word["apple"]["subtitle_id"] != by_word["cherry"]["subtitle_id"]

    async def test_detail_exposes_source_sentence_and_word_level(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        """来源句与级别不能靠前端猜。

        从视频收来的词只带 ``subtitle_id``，词条上的 ``context_sentence`` 是空的；
        详情必须用关联字幕的英文原句补上，否则每一行都显示「没有原句」。
        级别取 ECDICT 标记里的最高级（cherry 同时是四级与六级词 → 六级）。
        """
        video_id = await _seed_video([{"apple": ["cet4"], "cherry": ["cet4"]}])

        resp = await _collect(client, auth_headers, video_id, "cet4")
        detail = (await client.get(f"/api/v1/vocab-sets/{resp.json()['id']}", headers=auth_headers)).json()

        by_word = {w["word"]: w for w in detail["words"]}
        assert by_word["apple"]["context_sentence"] == "apple cherry"
        assert by_word["cherry"]["context_sentence"] == "apple cherry"
        assert by_word["apple"]["exam_level"] == "cet4"
        assert by_word["cherry"]["exam_level"] == "cet6"

    async def test_detail_words_without_subtitle_render_null_start_time(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        """Legacy words (or deleted subtitles) keep working: NULL subtitle_id →
        NULL start_time, the deep link is simply hidden by the frontend."""
        video_id = await _seed_video([{"apple": ["cet4"]}])
        resp = await _collect(client, auth_headers, video_id, "cet4")
        set_id = resp.json()["id"]

        async with TestSessionLocal() as db:
            row = (await db.execute(select(Vocabulary).where(Vocabulary.word == "apple"))).scalar_one()
            row.subtitle_id = None
            await db.commit()

        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        assert detail["words"][0]["subtitle_id"] is None
        assert detail["words"][0]["start_time"] is None

    async def test_collect_falls_back_to_cet4_without_preference(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video([{"apple": ["cet4"]}])

        resp = await _collect(client, auth_headers, video_id)

        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_level"] == "cet4"
        assert "四级" in data["message"]

    async def test_collect_uses_user_target_level(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        user_id = await _get_user_id(client, auth_headers)
        async with TestSessionLocal() as db:
            db.add(UserPreferences(user_id=user_id, target_exam="cet6"))
            await db.commit()
        video_id = await _seed_video([{"banana": ["cet6"]}])

        resp = await _collect(client, auth_headers, video_id)

        assert resp.json()["exam_level"] == "cet6"
        assert "六级" in resp.json()["message"]

    async def test_collect_explicit_level_overrides_preference(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        user_id = await _get_user_id(client, auth_headers)
        async with TestSessionLocal() as db:
            db.add(UserPreferences(user_id=user_id, target_exam="cet6"))
            await db.commit()
        video_id = await _seed_video([{"apple": ["cet4"]}])

        resp = await _collect(client, auth_headers, video_id, "cet4")

        assert resp.json()["exam_level"] == "cet4"

    async def test_collect_creates_ecdict_enriched_vocabulary_with_zero_ai_calls(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video([{"apple": ["cet4"], "apples": ["cet4"]}])

        resp = await _collect(client, auth_headers, video_id, "cet4")
        assert resp.status_code == 200

        user_id = await _get_user_id(client, auth_headers)
        async with TestSessionLocal() as db:
            rows = (await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id))).scalars().all()
        by_word = {v.word: v for v in rows}
        assert set(by_word) == {"apple", "apples"}
        for word in ("apple", "apples"):
            v = by_word[word]
            assert v.definition == "n. a round fruit"
            assert v.translation == "n. 苹果"
            assert v.part_of_speech == "n:100"
            assert v.ipa == "'æpl"
            assert v.mastery_level == "new"  # untouched by collect
            assert v.first_seen_at is not None
            assert v.video_id == video_id

    async def test_collect_truncates_overlong_part_of_speech(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video([{"longpos": ["cet4"]}])

        resp = await _collect(client, auth_headers, video_id, "cet4")
        assert resp.status_code == 200

        user_id = await _get_user_id(client, auth_headers)
        async with TestSessionLocal() as db:
            v = (
                (
                    await db.execute(
                        select(Vocabulary).where(Vocabulary.user_id == user_id, Vocabulary.word == "longpos")
                    )
                )
                .scalars()
                .one()
            )
        assert v.part_of_speech is not None
        assert len(v.part_of_speech) <= 20
        assert "n:1/v:2" in v.part_of_speech

    async def test_collect_video_missing_returns_404(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        resp = await _collect(client, auth_headers, "no-such-video", "cet4")
        assert resp.status_code == 404

    async def test_collect_repost_is_idempotent_with_no_duplicate_positions(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video(
            [
                {"apple": ["cet4"], "apples": ["cet4"]},
                {"cherry": ["cet4", "cet6"]},
            ]
        )

        first = (await _collect(client, auth_headers, video_id, "cet4")).json()
        assert first["existed"] is False

        second = (await _collect(client, auth_headers, video_id, "cet4")).json()
        assert second["existed"] is True
        assert second["added"] == 0
        assert second["total"] == 3
        assert second["message"] == "集合已存在，3 个单词"

        async with TestSessionLocal() as db:
            positions = (
                (
                    await db.execute(
                        select(VocabSetWord.position)
                        .where(VocabSetWord.set_id == first["id"])
                        .order_by(VocabSetWord.position.asc())
                    )
                )
                .scalars()
                .all()
            )
        assert positions == [1, 2, 3]

    async def test_collect_appends_only_new_tokens_continuing_positions(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video([{"apple": ["cet4"], "apples": ["cet4"]}])
        first = (await _collect(client, auth_headers, video_id, "cet4")).json()

        # A new subtitle appears with a fresh cet4 token.
        async with TestSessionLocal() as db:
            db.add(
                Subtitle(
                    video_id=video_id,
                    start_time=10.0,
                    end_time=14.0,
                    text_en="dragonfruit",
                    sentence_index=1,
                    word_levels={"dragonfruit": ["cet4"]},
                )
            )
            await db.commit()

        second = (await _collect(client, auth_headers, video_id, "cet4")).json()
        assert second["existed"] is True
        assert second["added"] == 1
        assert second["total"] == 3
        assert second["message"] == "已按四级筛选，1 个单词加入词汇本"

        detail = (await client.get(f"/api/v1/vocab-sets/{first['id']}", headers=auth_headers)).json()
        assert [w["word"] for w in detail["words"]] == ["apple", "apples", "dragonfruit"]
        assert [w["position"] for w in detail["words"]] == [1, 2, 3]


class TestListSets:
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/vocab-sets")
        assert resp.status_code == 401

    async def test_sort_unfinished_first_then_recent_activity(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        vid_a = await _seed_video([{"apple": ["cet4"]}], title="Video A")
        vid_b = await _seed_video([{"apple": ["cet4"]}], title="Video B")
        vid_c = await _seed_video([{"apple": ["cet4"]}], title="Video C")

        set_a = (await _collect(client, auth_headers, vid_a, "cet4")).json()
        set_b = (await _collect(client, auth_headers, vid_b, "cet4")).json()
        set_c = (await _collect(client, auth_headers, vid_c, "cet4")).json()

        # Finish set A (its single word judged known).
        detail_a = (await client.get(f"/api/v1/vocab-sets/{set_a['id']}", headers=auth_headers)).json()
        word_id_a = detail_a["words"][0]["set_word_id"]
        judge = await client.post(
            f"/api/v1/vocab-sets/{set_a['id']}/words/{word_id_a}/sieve",
            json={"known": True},
            headers=auth_headers,
        )
        assert judge.status_code == 200

        # Deterministic timestamps: C newest, B older, A oldest (and finished).
        t0 = datetime(2026, 9, 1, tzinfo=UTC)
        await _set_last_activity(set_c["id"], t0 + timedelta(hours=2))
        await _set_last_activity(set_b["id"], t0 + timedelta(hours=1))
        await _set_last_activity(set_a["id"], t0)

        resp = await client.get("/api/v1/vocab-sets", headers=auth_headers)
        assert resp.status_code == 200
        items = resp.json()
        assert [i["id"] for i in items] == [set_c["id"], set_b["id"], set_a["id"]]

        # Set fields: video title/thumbnail carried through; counts correct.
        by_id = {i["id"]: i for i in items}
        assert by_id[set_a["id"]]["mastered_count"] == 1
        assert by_id[set_a["id"]]["total"] == 1
        assert by_id[set_b["id"]]["mastered_count"] == 0
        assert by_id[set_b["id"]]["title"] == "Video B"
        assert by_id[set_b["id"]]["thumbnail_url"] == "https://img.example/thumb.jpg"
        assert by_id[set_c["id"]]["exam_level"] == "cet4"


class TestSetDetail:
    async def test_scope_filters(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        video_id = await _seed_video(
            [
                {"apple": ["cet4"], "apples": ["cet4"]},
                {"dragonfruit": ["cet4"]},
            ]
        )
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        w1, w2, _w3 = [w["set_word_id"] for w in detail["words"]]

        # Judge: word1 known, word2 unknown, word3 stays pending.
        await client.post(f"/api/v1/vocab-sets/{set_id}/words/{w1}/sieve", json={"known": True}, headers=auth_headers)
        await client.post(f"/api/v1/vocab-sets/{set_id}/words/{w2}/sieve", json={"known": False}, headers=auth_headers)

        all_words = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()["words"]
        assert [w["status"] for w in all_words] == ["known", "unknown", "pending"]
        assert all_words[0]["translation"] == "n. 苹果"
        assert all_words[0]["mastery_level"] == "mastered"

        unmastered = (await client.get(f"/api/v1/vocab-sets/{set_id}?scope=unmastered", headers=auth_headers)).json()[
            "words"
        ]
        assert [w["position"] for w in unmastered] == [2, 3]

        learning = (await client.get(f"/api/v1/vocab-sets/{set_id}?scope=learning", headers=auth_headers)).json()[
            "words"
        ]
        assert [w["position"] for w in learning] == [2]

    async def test_invalid_scope_returns_422(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        video_id = await _seed_video([{"apple": ["cet4"]}])
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]

        resp = await client.get(f"/api/v1/vocab-sets/{set_id}?scope=bogus", headers=auth_headers)

        assert resp.status_code == 422

    async def test_missing_set_returns_404(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/vocab-sets/no-such-set", headers=auth_headers)
        assert resp.status_code == 404

    async def test_other_users_set_returns_404_no_existence_leak(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video([{"apple": ["cet4"]}])
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        other_headers = await _other_auth_headers()

        resp = await client.get(f"/api/v1/vocab-sets/{set_id}", headers=other_headers)

        assert resp.status_code == 404


class TestSieve:
    async def _three_word_set(self, client: AsyncClient, auth_headers: dict) -> tuple[str, str, list[str]]:
        video_id = await _seed_video(
            [
                {"apple": ["cet4"], "apples": ["cet4"]},
                {"dragonfruit": ["cet4"]},
            ]
        )
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        return set_id, video_id, [w["set_word_id"] for w in detail["words"]]

    async def test_sieve_resumes_at_next_pending_word(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        set_id, _, word_ids = await self._three_word_set(client, auth_headers)

        first = (await client.get(f"/api/v1/vocab-sets/{set_id}/sieve", headers=auth_headers)).json()
        assert first["set_word_id"] == word_ids[0]
        assert first["position"] == 1
        assert first["sieved_count"] == 0
        assert first["total"] == 3
        assert first["completed"] is False
        assert first["word"]["word"] == "apple"

        await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_ids[0]}/sieve",
            json={"known": True},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_ids[1]}/sieve",
            json={"known": False},
            headers=auth_headers,
        )

        state = (await client.get(f"/api/v1/vocab-sets/{set_id}/sieve", headers=auth_headers)).json()
        assert state["set_word_id"] == word_ids[2]
        assert state["position"] == 3
        assert state["sieved_count"] == 2
        assert state["total"] == 3
        assert state["completed"] is False
        assert state["word"]["word"] == "dragonfruit"

    async def test_judge_known_marks_mastered(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        set_id, _, word_ids = await self._three_word_set(client, auth_headers)

        resp = await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_ids[0]}/sieve",
            json={"known": True},
            headers=auth_headers,
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "known"
        assert resp.json()["completed"] is False
        assert resp.json()["mastered_count"] == 1
        assert resp.json()["total"] == 3

        user_id = await _get_user_id(client, auth_headers)
        async with TestSessionLocal() as db:
            v = (
                (await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id, Vocabulary.word == "apple")))
                .scalars()
                .one()
            )
        assert v.mastery_level == "mastered"

    async def test_judge_unknown_sets_learning_only_from_new(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        user_id = await _get_user_id(client, auth_headers)
        # Pre-existing vocabulary with different mastery levels: collect must
        # reuse these rows, and unknown must not downgrade them.
        await _seed_vocab(
            user_id,
            [
                Vocabulary(user_id=user_id, word="sievea", mastery_level="new"),
                Vocabulary(user_id=user_id, word="sieveb", mastery_level="reviewing"),
                Vocabulary(user_id=user_id, word="sievec", mastery_level="mastered"),
            ],
        )
        video_id = await _seed_video(
            [
                {"sievea": ["cet4"], "sieveb": ["cet4"]},
                {"sievec": ["cet4"]},
            ]
        )
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        ids_by_word = {w["word"]: w["set_word_id"] for w in detail["words"]}

        for word in ("sievea", "sieveb", "sievec"):
            resp = await client.post(
                f"/api/v1/vocab-sets/{set_id}/words/{ids_by_word[word]}/sieve",
                json={"known": False},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == "unknown"

        async with TestSessionLocal() as db:
            rows = (await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id))).scalars().all()
        mastery = {v.word: v.mastery_level for v in rows}
        assert mastery == {"sievea": "learning", "sieveb": "reviewing", "sievec": "mastered"}

    async def test_judge_word_not_in_set_returns_404(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        set_id, _, word_ids = await self._three_word_set(client, auth_headers)
        other_set_id, _, _ = await self._three_word_set(client, auth_headers)

        resp = await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_ids[0]}/sieve",
            json={"known": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # A word id from another set does not belong here.
        resp = await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_ids[0]}/sieve".replace(set_id, other_set_id),
            json={"known": True},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_completion_emits_exactly_one_learned_words_event(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        set_id, video_id, word_ids = await self._three_word_set(client, auth_headers)
        user_id = await _get_user_id(client, auth_headers)

        # Sieve pass: two known, one 「不会」 → that word lands in the 待学清单
        # (unknown), so the set is NOT complete yet (§4.5).
        for i, sw_id in enumerate(word_ids):
            resp = await client.post(
                f"/api/v1/vocab-sets/{set_id}/words/{sw_id}/sieve",
                json={"known": i != 1},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["completed"] is False

        assert resp.json()["mastered_count"] == 2
        assert resp.json()["total"] == 3

        # Sieve state: nothing pending, but one word still awaits learning.
        state = (await client.get(f"/api/v1/vocab-sets/{set_id}/sieve", headers=auth_headers)).json()
        assert state["completed"] is False
        assert state["set_word_id"] is None
        assert state["word"] is None
        assert state["sieved_count"] == 3
        assert state["pending_count"] == 0
        assert state["unknown_count"] == 1
        assert state["mastered_count"] == 2

        # 学完待学清单 → 闭环：mark the unknown word learned.
        resp = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_ids[1]}/learned", headers=auth_headers)
        assert resp.status_code == 200
        final = resp.json()
        assert final["status"] == "learned"
        assert final["completed"] is True
        assert final["mastered_count"] == 3
        assert final["total"] == 3

        async with TestSessionLocal() as db:
            events = (
                (
                    await db.execute(
                        select(LearningEvent).where(
                            LearningEvent.user_id == user_id,
                            LearningEvent.event_type == "learned_words",
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(events) == 1
            event = events[0]
            assert event.event_value == 3  # the set total
            assert event.video_id == video_id
            assert event.event_metadata["source"] == "vocab_set"
            assert event.event_metadata["set_id"] == set_id

            profile = (
                (await db.execute(select(UserLearningProfile).where(UserLearningProfile.user_id == user_id)))
                .scalars()
                .one()
            )
            assert profile.today_words_learned == 3

        # Re-marking after closure must NOT emit a second event.
        resp = await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_ids[0]}/sieve",
            json={"known": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["completed"] is True

        async with TestSessionLocal() as db:
            count = (
                await db.execute(
                    select(func.count(LearningEvent.id)).where(
                        LearningEvent.user_id == user_id,
                        LearningEvent.event_type == "learned_words",
                    )
                )
            ).scalar_one()
        assert count == 1


class TestMasteredExitsReviewQueues:
    """Tri-state semantics: mastered words never appear in due counts/queues."""

    async def _seed_mixed_words(self, client: AsyncClient, auth_headers: dict) -> None:
        user_id = await _get_user_id(client, auth_headers)
        now = datetime.now(UTC)
        await _seed_vocab(
            user_id,
            [
                Vocabulary(
                    user_id=user_id,
                    word="due-mastered",
                    mastery_level="mastered",
                    next_review_at=now - timedelta(days=1),
                ),
                Vocabulary(
                    user_id=user_id,
                    word="fresh-mastered",
                    mastery_level="mastered",
                    next_review_at=None,
                ),
                Vocabulary(
                    user_id=user_id,
                    word="due-learning",
                    mastery_level="learning",
                    next_review_at=now - timedelta(days=1),
                ),
                Vocabulary(user_id=user_id, word="due-new", mastery_level="new", next_review_at=None),
            ],
        )

    async def test_due_only_list_excludes_mastered(self, client: AsyncClient, auth_headers: dict):
        await self._seed_mixed_words(client, auth_headers)

        resp = await client.get("/api/v1/vocabulary?due_only=true", headers=auth_headers)

        assert resp.status_code == 200
        words = {w["word"] for w in resp.json()["items"]}
        assert words == {"due-learning", "due-new"}

    async def test_stats_due_count_excludes_mastered(self, client: AsyncClient, auth_headers: dict):
        await self._seed_mixed_words(client, auth_headers)

        resp = await client.get("/api/v1/vocabulary/stats", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["mastered_count"] == 2
        assert data["due_count"] == 2

    async def test_practice_due_only_excludes_mastered(self, client: AsyncClient, auth_headers: dict):
        await self._seed_mixed_words(client, auth_headers)

        resp = await client.get("/api/v1/vocabulary/practice?due_only=true&count=10", headers=auth_headers)

        assert resp.status_code == 200
        words = {i["word"] for i in resp.json()["items"]}
        assert words == {"due-learning", "due-new"}


class TestUnmarkLearned:
    """S8: 取消「已掌握」—— mark_learned / sieve「会」的逆操作。

    口径（按 build_daily_session 反推）：词行回 learning 且次日到期 ——
    new 队列只取 ``mastery == new``（回 new 会立刻进当日新词队列），
    复习队列只取到期且 ``mastery ∉ {new, mastered}`` 的词。
    """

    async def _one_word_learned_set(self, client: AsyncClient, auth_headers: dict) -> tuple[str, str]:
        video_id = await _seed_video([{"apple": ["cet4"]}])
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        word_id = detail["words"][0]["set_word_id"]
        resp = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/learned", headers=auth_headers)
        assert resp.status_code == 200
        return set_id, word_id

    async def test_unmark_learned_reverts_status_and_mastery(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        set_id, word_id = await self._one_word_learned_set(client, auth_headers)
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/unmark", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unknown"
        assert data["completed"] is False
        assert data["mastered_count"] == 0
        assert data["total"] == 1

        async with TestSessionLocal() as db:
            v = (
                (await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id, Vocabulary.word == "apple")))
                .scalars()
                .one()
            )
        assert v.mastery_level == "learning"
        assert v.interval_days == 1
        next_review_at = v.next_review_at
        if next_review_at is not None and next_review_at.tzinfo is None:
            next_review_at = next_review_at.replace(tzinfo=UTC)
        assert next_review_at is not None and next_review_at > datetime.now(UTC)

        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        assert detail["words"][0]["status"] == "unknown"
        assert detail["mastered_count"] == 0

    async def test_unmark_after_sieve_known_reopens_set_without_second_event(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        """闭环 → 取消 → 重学：learned_words 事件与今日累计不得重复计数。"""
        video_id = await _seed_video([{"apple": ["cet4"]}])
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        word_id = detail["words"][0]["set_word_id"]
        user_id = await _get_user_id(client, auth_headers)

        judge = await client.post(
            f"/api/v1/vocab-sets/{set_id}/words/{word_id}/sieve",
            json={"known": True},
            headers=auth_headers,
        )
        assert judge.json()["completed"] is True

        unmark = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/unmark", headers=auth_headers)
        assert unmark.json()["completed"] is False

        relearn = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/learned", headers=auth_headers)
        assert relearn.json()["completed"] is True

        async with TestSessionLocal() as db:
            events = (
                (
                    await db.execute(
                        select(LearningEvent).where(
                            LearningEvent.user_id == user_id,
                            LearningEvent.event_type == "learned_words",
                        )
                    )
                )
                .scalars()
                .all()
            )
            profile = (
                (await db.execute(select(UserLearningProfile).where(UserLearningProfile.user_id == user_id)))
                .scalars()
                .one()
            )
        assert len(events) == 1
        assert profile.today_words_learned == 1

    async def test_unmarked_word_not_in_today_queues(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        set_id, word_id = await self._one_word_learned_set(client, auth_headers)

        resp = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/unmark", headers=auth_headers)
        assert resp.status_code == 200

        daily = (await client.get("/api/v1/vocabulary/daily-session", headers=auth_headers)).json()
        new_words = [w["word"] for w in daily["new_words"]]
        review_words = [w["word"] for w in daily["review_words"]]
        assert "apple" not in new_words
        assert "apple" not in review_words

    async def test_unmark_non_mastered_word_is_idempotent_noop(
        self, client: AsyncClient, auth_headers: dict, ecdict_only
    ):
        video_id = await _seed_video([{"apple": ["cet4"]}])
        set_id = (await _collect(client, auth_headers, video_id, "cet4")).json()["id"]
        detail = (await client.get(f"/api/v1/vocab-sets/{set_id}", headers=auth_headers)).json()
        word_id = detail["words"][0]["set_word_id"]
        user_id = await _get_user_id(client, auth_headers)

        resp = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/unmark", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

        async with TestSessionLocal() as db:
            v = (
                (await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id, Vocabulary.word == "apple")))
                .scalars()
                .one()
            )
        assert v.mastery_level == "new"
        assert v.next_review_at is None

    async def test_unmark_other_users_set_returns_404(self, client: AsyncClient, auth_headers: dict, ecdict_only):
        set_id, word_id = await self._one_word_learned_set(client, auth_headers)
        other_headers = await _other_auth_headers()

        resp = await client.post(f"/api/v1/vocab-sets/{set_id}/words/{word_id}/unmark", headers=other_headers)
        assert resp.status_code == 404

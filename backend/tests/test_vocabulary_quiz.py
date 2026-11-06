"""Tests for vocabulary practice: distractor selection (S4) and submission.

The old ``submit_quiz`` function has been removed — quiz functionality is now
unified into ``practice_service.build_vocabulary_drill`` and
``practice_service.submit_practice_results``.  The skip-prevention rule is
tested via the practice submit endpoint instead.

S4 covers ``select_distractors`` (设计文档 §8): the priority ladder
(same-video → edit-distance → ECDICT), the hard constraints (exactly 4
options, same POS/level, synonym/containment exclusion, dedupe, shuffle),
and the ECDICT fallback that lets a 2-word wordbook still produce full
4-option questions.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.learning import Vocabulary
from app.models.user import RoleType, User
from app.services import ecdict, practice_service
from tests.conftest import TestSessionLocal, hash_password


def _cand(word, translation, pos="", levels=(), video_id=None, bnc=0):
    return practice_service.DistractorCandidate(
        word=word,
        translation=translation,
        pos=practice_service._pos_tokens(pos),
        levels=frozenset(levels),
        video_id=video_id,
        bnc=bnc,
    )


def _select(target_word, correct, *, same_video=(), vocab_rest=(), ecdict_pool=(), pos="n", levels=("cet4",)):
    return practice_service.select_distractors(
        target_word=target_word,
        correct_translation=correct,
        same_video=list(same_video),
        vocab_rest=list(vocab_rest),
        ecdict_pool=list(ecdict_pool),
        target_pos=practice_service._pos_tokens(pos),
        target_levels=frozenset(levels),
    )


class TestSelectDistractors:
    def test_prefers_same_video_same_level_same_pos(self):
        same_video = [
            _cand("gather", "聚集", pos="v", levels=["cet4"]),
            _cand("obtain", "获得", pos="v", levels=["cet4"]),
            _cand("require", "要求", pos="v", levels=["cet4"]),
        ]
        # Wordbook-wide candidates would also qualify — must NOT be used while
        # the same-video pool can fill all three slots.
        vocab_rest = [_cand("acquire", "习得", pos="v", levels=["cet4"])]

        out = _select("collect", "收集", same_video=same_video, vocab_rest=vocab_rest, pos="v")

        assert set(out) == {"聚集", "获得", "要求"}
        assert len(out) == 3

    def test_falls_back_to_edit_distance_words(self):
        # same-video empty → priority 2: wordbook words 2~4 edits away.
        vocab_rest = [
            _cand("record", "记录", pos="v", levels=["cet4"]),  # report → record = 2 edits
            _cand("regard", "看待", pos="v", levels=["cet4"]),  # report → regard = 3 edits
            _cand("reply", "回复", pos="v", levels=["cet4"]),  # report → reply = 3 edits
            _cand("understand", "理解", pos="v", levels=["cet4"]),  # too far — excluded
            _cand("idea", "主意", pos="n", levels=["cet4"]),  # wrong POS — excluded
        ]

        out = _select("report", "报告", vocab_rest=vocab_rest, pos="v")

        assert set(out) == {"记录", "看待", "回复"}

    def test_ecdict_fallback_prefers_high_frequency(self):
        ecdict_pool = [
            _cand("obtain", "获得", pos="v", levels=["cet4"], bnc=1200),
            _cand("acquire", "习得", pos="v", levels=["cet4"], bnc=3000),
            _cand("gather", "聚集", pos="v", levels=["cet4"], bnc=800),
            _cand("derive", "衍生", pos="v", levels=["cet4"], bnc=2000),
        ]

        out = _select("collect", "收集", ecdict_pool=ecdict_pool, pos="v")

        # Lowest BNC rank first until three slots are filled.
        assert set(out) == {"聚集", "获得", "衍生"}

    def test_excludes_synonym_and_containment(self):
        same_video = [
            _cand("object", "事物", pos="n", levels=["cet4"]),  # equal → excluded
            _cand("item", "事物；东西", pos="n", levels=["cet4"]),  # containment → excluded
            _cand("affair", "事务", pos="n", levels=["cet4"]),
            _cand("matter", "事情", pos="n", levels=["cet4"]),
            _cand("substance", "物质", pos="n", levels=["cet4"]),
        ]

        out = _select("thing", "事物", same_video=same_video)

        assert "事物" not in out
        assert "事物；东西" not in out
        assert set(out) == {"事务", "事情", "物质"}

    def test_dedupes_identical_translations(self):
        vocab_rest = [
            _cand("gain", "获得", pos="v", levels=["cet4"]),
            _cand("obtain", "获得", pos="v", levels=["cet4"]),
            _cand("acquire", "取得", pos="v", levels=["cet4"]),
            _cand("derive", "赢得", pos="v", levels=["cet4"]),
        ]

        out = _select("earn", "挣得", vocab_rest=vocab_rest, pos="v")

        assert out.count("获得") == 1
        assert len(out) == 3

    def test_relaxes_constraints_to_fill_slots(self):
        # Nothing matches level/POS — the relaxation pass must still fill 3
        # slots so the question can be built.
        vocab_rest = [
            _cand("abstract", "抽象的", pos="a", levels=["gre"]),
            _cand("paradigm", "范式", pos="n", levels=["gre"]),
            _cand("empirical", "经验的", pos="a", levels=["gre"]),
        ]

        out = _select("collect", "收集", vocab_rest=vocab_rest, pos="v", levels=("cet4",))

        assert set(out) == {"抽象的", "范式", "经验的"}

    def test_no_correct_translation_yields_no_distractors(self):
        out = _select("word", "")

        assert out == []

    def test_option_order_is_shuffled(self):
        positions = set()
        for _ in range(40):
            item = practice_service._build_recognition_item("word", "正确", "/wɜːd/", ["甲", "乙", "丙"])
            assert item["options"] is not None
            assert len(item["options"]) == 4
            positions.add(item["options"].index("正确"))

        # The correct answer must not sit at a fixed position across questions.
        assert len(positions) > 1


class TestPosParsing:
    def test_ecdict_style_and_full_words_share_tokens(self):
        assert practice_service._pos_tokens("n:46/v:32") == {"n", "v"}
        assert practice_service._pos_tokens("noun/verb") == {"n", "v"}
        assert practice_service._pos_tokens("adj") == {"a"}
        assert practice_service._pos_tokens("i:10/n:1/r:87/j:1/v:1") >= {"n", "v"}

    def test_empty_pos(self):
        assert practice_service._pos_tokens(None) == frozenset()
        assert practice_service._pos_tokens("") == frozenset()


def _fake_lookup(token: str):
    """Every word looks like a cet4 noun so POS/level gates pass uniformly."""
    return {"lemma": token, "levels": ["cet4"], "pos": "n:99", "bnc": 1000}


def _fake_entries():
    return [
        {"lemma": w, "translation": t, "pos": "n:99", "levels": ["cet4"], "bnc": 500}
        for w, t in (("river", "河流"), ("mountain", "山"), ("forest", "森林"), ("island", "岛屿"))
    ]


@pytest.mark.asyncio
async def test_drill_builds_full_options_with_ecdict_fallback(fake_redis, monkeypatch):
    """词库只有 2 个词时仍能出 4 选项题（ECDICT 兜底），且选项满足硬约束。"""
    monkeypatch.setattr(ecdict, "is_available", lambda: True)
    monkeypatch.setattr(ecdict, "lookup", _fake_lookup)
    monkeypatch.setattr(ecdict, "entries", _fake_entries)

    async with TestSessionLocal() as db:
        user = User(
            phone="13800138020",
            hashed_password=hash_password("Vocabpass1!"),
            name="Quiz",
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        uid = user.id

    async with TestSessionLocal() as db:
        for word, translation in (("apple", "苹果"), ("banana", "香蕉")):
            db.add(Vocabulary(user_id=uid, word=word, translation=translation, definition="a fruit"))
        await db.commit()
        rows = (await db.execute(select(Vocabulary).where(Vocabulary.user_id == uid))).scalars().all()
        assert len(rows) == 2

    async with TestSessionLocal() as db:
        items = await practice_service.build_vocabulary_drill(db, uid, count=2)

    recognition = [i for i in items if i["category"] == "recognition"]
    assert recognition, "new words must produce recognition items"
    for item in recognition:
        assert item["options"] is not None
        assert len(item["options"]) == 4
        assert len(set(item["options"])) == 4
        assert item["options"].count(item["answer"]) == 1
        correct_key = practice_service._translation_key(item["answer"])
        for opt in item["options"]:
            if opt != item["answer"]:
                key = practice_service._translation_key(opt)
                assert correct_key not in key and key not in correct_key


async def _submit_user(phone: str) -> str:
    async with TestSessionLocal() as db:
        user = User(
            phone=phone,
            hashed_password=hash_password("Vocabpass1!"),
            name="Submit",
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user.id


async def _row(user_id: str, word: str) -> Vocabulary:
    async with TestSessionLocal() as db:
        return (
            await db.execute(select(Vocabulary).where(Vocabulary.user_id == user_id, Vocabulary.word == word))
        ).scalar_one()


class TestSubmitPracticeResults:
    """到期复习词经 /practice/submit 提交（S5 合并循环的真实路径）走 DEC-057 分档；
    自动添加 / 仍为 new 的词保持冻结的 SM-2 更新（S6 补票）。"""

    async def _seed_review_word(self, user_id: str, word: str, mastery_level: str = "learning", **fields) -> None:
        async with TestSessionLocal() as db:
            db.add(Vocabulary(user_id=user_id, word=word, mastery_level=mastery_level, **fields))
            await db.commit()

    @pytest.mark.asyncio
    async def test_review_word_wrong_answer_records_error_fields(self, fake_redis):
        uid = await _submit_user("13800138031")
        await self._seed_review_word(uid, "reviewme", review_count=2, interval_days=7)

        async with TestSessionLocal() as db:
            result = await practice_service.submit_practice_results(db, uid, [{"word": "reviewme", "correct": False}])
        assert result == {"updated": 1, "auto_added": 0}

        row = await _row(uid, "reviewme")
        assert row.wrong_count == 1
        assert row.last_wrong_at is not None
        assert row.interval_days == 1  # 复习时答错 → 回到次日

    @pytest.mark.asyncio
    async def test_review_word_wrong_answer_at_graduation_line_stays_reviewing(self, fake_redis):
        uid = await _submit_user("13800138036")
        await self._seed_review_word(uid, "wrongcap", review_count=5, mastery_level="reviewing", interval_days=7)

        async with TestSessionLocal() as db:
            await practice_service.submit_practice_results(db, uid, [{"word": "wrongcap", "correct": False}])

        row = await _row(uid, "wrongcap")
        assert row.review_count == 6
        assert row.mastery_level == "reviewing"  # 错词不得毕业，次日复习仍可达

    @pytest.mark.asyncio
    async def test_review_word_correct_answer_at_graduation_line_masters(self, fake_redis):
        uid = await _submit_user("13800138037")
        await self._seed_review_word(uid, "gradme", review_count=5, mastery_level="reviewing", interval_days=7)

        async with TestSessionLocal() as db:
            await practice_service.submit_practice_results(db, uid, [{"word": "gradme", "correct": True}])

        row = await _row(uid, "gradme")
        assert row.mastery_level == "mastered"  # 答对仍按次数毕业

    @pytest.mark.asyncio
    async def test_new_word_wrong_answer_falls_back_to_new(self, fake_redis):
        """SM-2 冻结路径答错重置 review_count → mastery 回落 new，不毕业也不消失。"""
        uid = await _submit_user("13800138038")
        async with TestSessionLocal() as db:
            db.add(Vocabulary(user_id=uid, word="legacycap", mastery_level="new", review_count=5))
            await db.commit()

        async with TestSessionLocal() as db:
            await practice_service.submit_practice_results(db, uid, [{"word": "legacycap", "correct": False}])

        row = await _row(uid, "legacycap")
        assert row.review_count == 0
        assert row.mastery_level == "new"

    @pytest.mark.asyncio
    async def test_review_word_correct_answer_climbs_error_ladder(self, fake_redis):
        uid = await _submit_user("13800138032")
        now = datetime.now(UTC)
        await self._seed_review_word(
            uid,
            "ladderme",
            review_count=2,
            interval_days=1,
            wrong_count=1,
            last_wrong_at=now - timedelta(days=3),
        )

        async with TestSessionLocal() as db:
            await practice_service.submit_practice_results(db, uid, [{"word": "ladderme", "correct": True}])

        row = await _row(uid, "ladderme")
        assert row.interval_days == 2  # 错误阶梯 1 → 2
        assert row.wrong_count == 1  # 答对不增错误数
        assert row.correct_count == 1  # 只计一次（apply_review 内已计，事件扫不重复）

    @pytest.mark.asyncio
    async def test_review_word_wrong_recently_stays_next_day_after_correct(self, fake_redis):
        uid = await _submit_user("13800138033")
        now = datetime.now(UTC)
        await self._seed_review_word(
            uid,
            "recentwrong",
            review_count=3,
            interval_days=5,
            wrong_count=2,
            last_wrong_at=now - timedelta(hours=2),
        )

        async with TestSessionLocal() as db:
            await practice_service.submit_practice_results(db, uid, [{"word": "recentwrong", "correct": True}])

        row = await _row(uid, "recentwrong")
        assert row.interval_days == 1  # 24h 内错过 → 次日重现

    @pytest.mark.asyncio
    async def test_new_word_submission_keeps_legacy_sm2_path(self, fake_redis):
        uid = await _submit_user("13800138034")
        async with TestSessionLocal() as db:
            db.add(Vocabulary(user_id=uid, word="brandnew", mastery_level="new"))
            await db.commit()

        async with TestSessionLocal() as db:
            await practice_service.submit_practice_results(db, uid, [{"word": "brandnew", "correct": True}])

        row = await _row(uid, "brandnew")
        assert row.interval_days == 1  # SM-2 首次答对 = 1 天（新算法会给 3 天）
        assert row.ease_factor == pytest.approx(2.6)  # SM-2 仍在更新 ease_factor
        assert row.wrong_count == 0
        assert row.correct_count == 1

    @pytest.mark.asyncio
    async def test_auto_added_word_keeps_legacy_sm2_path(self, fake_redis):
        uid = await _submit_user("13800138035")

        async with TestSessionLocal() as db:
            result = await practice_service.submit_practice_results(db, uid, [{"word": "autoword", "correct": True}])
        assert result == {"updated": 1, "auto_added": 1}

        row = await _row(uid, "autoword")
        assert row.mastery_level == "learning"
        assert row.interval_days == 1
        assert row.ease_factor == pytest.approx(2.6)

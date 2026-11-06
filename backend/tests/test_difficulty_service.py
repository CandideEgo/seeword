"""Tests for video difficulty auto-computation.

Covers the pure computation logic (超纲率 → CEFR mapping) and the async DB
integration (compute_video_difficulty writes only when null).
"""

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models.subtitle import Subtitle
from app.models.user import RoleType, User
from app.models.video import Video, VideoStatus
from app.services.difficulty_service import (
    beyond_basic_ratio,
    compute_difficulty_from_word_levels,
    compute_video_difficulty,
)

# --- Pure computation tests ---


def _wl(basic: int, beyond: int, beyond_level: str = "gaoKao") -> dict:
    """word_levels dict with `basic` 中考 words and `beyond` words at `beyond_level`."""
    out = {f"b{i}": ["zhongkao"] for i in range(basic)}
    out.update({f"x{i}": [beyond_level] for i in range(beyond)})
    return out


class TestBeyondBasicRatio:
    """Unit tests for the raw 超纲率 statistic."""

    def test_empty_returns_none(self):
        assert beyond_basic_ratio([]) is None

    def test_all_none_returns_none(self):
        assert beyond_basic_ratio([None, None, None]) is None

    def test_below_min_occurrences_returns_none(self):
        assert beyond_basic_ratio([_wl(10, 10)]) is None

    def test_all_basic_is_zero(self):
        assert beyond_basic_ratio([_wl(40, 0)]) == 0.0

    def test_all_beyond_is_one(self):
        assert beyond_basic_ratio([_wl(0, 40)]) == 1.0

    def test_ratio_is_share_of_occurrences(self):
        assert beyond_basic_ratio([_wl(70, 30)]) == pytest.approx(0.3)

    def test_word_uses_lowest_listing(self):
        # A word in both 中考 and IELTS is met at 中考 — it must NOT count as 超纲.
        wl = {f"w{i}": ["zhongkao", "ielts"] for i in range(40)}
        assert beyond_basic_ratio([wl]) == 0.0

    def test_word_above_basic_counts_even_when_also_in_a_higher_list(self):
        # A word in both CET4 and IELTS is met at CET4 — above 中考, so 超纲.
        wl = {f"w{i}": ["cet4", "ielts"] for i in range(40)}
        assert beyond_basic_ratio([wl]) == 1.0

    def test_words_absent_from_every_list_are_ignored(self):
        # 20 unknown + 40 basic → ratio measured over the 40 known occurrences.
        wl = {f"u{i}": [] for i in range(20)}
        wl.update(_wl(40, 0))
        assert beyond_basic_ratio([wl]) == 0.0

    def test_occurrences_accumulate_across_subtitles(self):
        # 中考 words repeated across sentences each count once per sentence.
        assert beyond_basic_ratio([_wl(20, 10), _wl(20, 10)]) == pytest.approx(20 / 60)


class TestComputeDifficultyFromWordLevels:
    """Unit tests for the pure 超纲率 → CEFR mapping."""

    def test_empty_list_returns_none(self):
        assert compute_difficulty_from_word_levels([]) is None

    def test_too_few_occurrences_returns_none(self):
        assert compute_difficulty_from_word_levels([_wl(5, 5)]) is None

    @pytest.mark.parametrize(
        ("basic", "beyond", "expected"),
        [
            (84, 16, "A1"),  # 0.16
            (83, 17, "A2"),  # 0.17 — A1/A2 cut
            (75, 25, "A2"),  # 0.25
            (74, 26, "B1"),  # 0.26 — A2/B1 cut
            (71, 29, "B1"),  # 0.29
            (70, 30, "B2"),  # 0.30 — B1/B2 cut
            (54, 46, "B2"),  # 0.46
            (53, 47, "C1"),  # 0.47 — B2/C1 cut
            (46, 54, "C1"),  # 0.54
            (45, 55, "C2"),  # 0.55 — C1/C2 cut
        ],
    )
    def test_ratio_bands(self, basic, beyond, expected):
        assert compute_difficulty_from_word_levels([_wl(basic, beyond)]) == expected

    def test_every_level_key_beyond_basic_counts_the_same(self):
        for level in ("gaoKao", "cet4", "cet6", "ky", "ielts", "toefl", "gre"):
            assert compute_difficulty_from_word_levels([_wl(70, 30, level)]) == "B2"

    def test_word_with_multiple_levels_takes_min(self):
        # Regression: the pre-DEC-043 code took max, so any word also listed in
        # IELTS scored as C1/C2 and the whole corpus collapsed to C2.
        wl = {f"w{i}": ["zhongkao", "gre"] for i in range(40)}
        assert compute_difficulty_from_word_levels([wl]) == "A1"

    def test_empty_level_lists_ignored(self):
        wl = {f"e{i}": [] for i in range(10)}
        wl.update(_wl(70, 30))
        assert compute_difficulty_from_word_levels([wl]) == "B2"


# --- DB integration tests ---


async def _ensure_user(db_session) -> User:
    """Get or create the test user."""
    user = (await db_session.execute(select(User).where(User.phone == "13800138000"))).scalar_one_or_none()
    if user is None:
        user = User(
            phone="13800138000",
            hashed_password=hash_password("Testpass123!"),
            name="Test User",
            role=RoleType.user,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    return user


async def _make_video_with_subtitles(db_session, word_levels_list: list[dict | None]) -> str:
    """Create a video + subtitles with given word_levels. Returns video_id."""
    user = await _ensure_user(db_session)
    v = Video(
        title="Difficulty Test Video",
        source_url="https://www.youtube.com/watch?v=difficulty_test",
        video_source="imported",
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        user_id=user.id,
    )
    db_session.add(v)
    await db_session.flush()

    for i, wl in enumerate(word_levels_list):
        db_session.add(
            Subtitle(
                video_id=v.id,
                start_time=i * 3.0,
                end_time=(i + 1) * 3.0,
                text_en=f"Sentence {i}",
                sentence_index=i,
                word_levels=wl,
            )
        )
    await db_session.commit()
    return v.id


@pytest.mark.asyncio
async def test_compute_video_difficulty_writes_level(db_session):
    """Videos with null difficulty get a computed CEFR level."""
    video_id = await _make_video_with_subtitles(db_session, [_wl(70, 30)])

    result = await compute_video_difficulty(db_session, video_id)
    assert result == "B2"

    # Verify persisted
    video = await db_session.scalar(select(Video).where(Video.id == video_id))
    assert video.difficulty_level == "B2"


@pytest.mark.asyncio
async def test_compute_video_difficulty_does_not_overwrite(db_session):
    """Manually-set difficulty_level is never overwritten."""
    video_id = await _make_video_with_subtitles(db_session, [_wl(70, 30)])

    # Manually set to C1
    video = await db_session.scalar(select(Video).where(Video.id == video_id))
    video.difficulty_level = "C1"
    await db_session.commit()

    result = await compute_video_difficulty(db_session, video_id)
    assert result == "C1"  # unchanged


@pytest.mark.asyncio
async def test_compute_video_difficulty_insufficient_data(db_session):
    """Videos with too few annotated occurrences keep null difficulty."""
    video_id = await _make_video_with_subtitles(db_session, [_wl(10, 10)])

    result = await compute_video_difficulty(db_session, video_id)
    assert result is None

    video = await db_session.scalar(select(Video).where(Video.id == video_id))
    assert video.difficulty_level is None


@pytest.mark.asyncio
async def test_compute_video_difficulty_no_subtitles(db_session):
    """Videos with no subtitles keep null difficulty."""
    user = await _ensure_user(db_session)
    v = Video(
        title="No Subs Video",
        source_url="https://www.youtube.com/watch?v=no_subs",
        video_source="imported",
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        user_id=user.id,
    )
    db_session.add(v)
    await db_session.commit()

    result = await compute_video_difficulty(db_session, v.id)
    assert result is None

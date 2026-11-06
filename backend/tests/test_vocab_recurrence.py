"""Tests for vocabulary recurrence recommendation boost (Sprint 3, Task 3.2).

Verifies that videos containing words the user is actively learning get a
ranking boost in the recommendation feed.
"""

import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models.learning import Vocabulary
from app.models.subtitle import Subtitle
from app.models.user import RoleType, User
from app.models.video import Video, VideoStatus
from app.services.recommendation_service import (
    _user_learning_words,
    _vocab_recurrence_boosts,
)


async def _setup_user(db_session) -> str:
    """Get or create the test user, return user id."""
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
    return user.id


async def _make_video_with_words(db_session, words: list[str], source_suffix: str = "") -> Video:
    """Create a video with subtitles containing the given words in word_levels."""
    user_id = await _setup_user(db_session)
    v = Video(
        title=f"Vocab Video {source_suffix}",
        source_url=f"https://www.youtube.com/watch?v=vocab_test{source_suffix}",
        video_source="imported",
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        user_id=user_id,
    )
    db_session.add(v)
    await db_session.flush()

    # Create subtitle with word_levels containing the given words
    wl = {w.lower(): ["cet4"] for w in words}
    db_session.add(
        Subtitle(
            video_id=v.id,
            start_time=0.0,
            end_time=5.0,
            text_en=" ".join(words),
            sentence_index=0,
            word_levels=wl,
        )
    )
    await db_session.commit()
    return v


async def _add_vocab(db_session, user_id: str, words: list[str], mastery: str = "learning"):
    """Add vocabulary entries for the user."""
    for w in words:
        db_session.add(
            Vocabulary(
                user_id=user_id,
                word=w.lower(),
                mastery_level=mastery,
                translation=f"翻译_{w}",
            )
        )
    await db_session.commit()


@pytest.mark.asyncio
async def test_user_learning_words_returns_learning_and_reviewing(db_session):
    """_user_learning_words returns words with mastery learning or reviewing."""
    user_id = await _setup_user(db_session)
    await _add_vocab(db_session, user_id, ["apple", "banana"], mastery="learning")
    await _add_vocab(db_session, user_id, ["cherry"], mastery="reviewing")
    await _add_vocab(db_session, user_id, ["date"], mastery="mastered")  # should NOT appear

    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    words = await _user_learning_words(db_session, user)

    assert "apple" in words
    assert "banana" in words
    assert "cherry" in words
    assert "date" not in words  # mastered excluded


@pytest.mark.asyncio
async def test_user_learning_words_empty_for_no_vocab(db_session):
    """Users with no vocabulary get an empty set."""
    user_id = await _setup_user(db_session)
    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    words = await _user_learning_words(db_session, user)
    assert words == set()


@pytest.mark.asyncio
async def test_vocab_recurrence_boost_positive_match(db_session):
    """Videos containing learning words get a positive boost."""
    user_id = await _setup_user(db_session)
    await _add_vocab(db_session, user_id, ["algorithm", "neural", "network"])

    # Video contains 2 of the 3 learning words
    video = await _make_video_with_words(db_session, ["algorithm", "neural", "deep", "learning"])

    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    vocab_words = await _user_learning_words(db_session, user)
    boosts = await _vocab_recurrence_boosts(db_session, vocab_words, [video])

    assert video.id in boosts
    assert boosts[video.id] > 0
    # 2 matches / 3 total words * 5.0 max = ~3.33
    assert abs(boosts[video.id] - (2 / 3) * 5.0) < 0.01


@pytest.mark.asyncio
async def test_vocab_recurrence_boost_no_match(db_session):
    """Videos with no matching words get no boost."""
    user_id = await _setup_user(db_session)
    await _add_vocab(db_session, user_id, ["quantum", "physics"])

    # Video contains unrelated words
    video = await _make_video_with_words(db_session, ["cooking", "recipe", "food"])

    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    vocab_words = await _user_learning_words(db_session, user)
    boosts = await _vocab_recurrence_boosts(db_session, vocab_words, [video])

    assert video.id not in boosts


@pytest.mark.asyncio
async def test_vocab_recurrence_boost_empty_vocab(db_session):
    """Empty vocab words → no boosts computed."""
    video = await _make_video_with_words(db_session, ["hello", "world"])
    boosts = await _vocab_recurrence_boosts(db_session, set(), [video])
    assert boosts == {}


@pytest.mark.asyncio
async def test_vocab_recurrence_boost_multiple_videos(db_session):
    """Boost is proportional to match count across multiple videos."""
    user_id = await _setup_user(db_session)
    await _add_vocab(db_session, user_id, ["alpha", "beta", "gamma", "delta"])

    # Video A: 3 matches; Video B: 1 match
    video_a = await _make_video_with_words(db_session, ["alpha", "beta", "gamma", "other"], "a")
    video_b = await _make_video_with_words(db_session, ["delta", "unrelated", "words"], "b")

    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    vocab_words = await _user_learning_words(db_session, user)
    boosts = await _vocab_recurrence_boosts(db_session, vocab_words, [video_a, video_b])

    assert boosts[video_a.id] > boosts[video_b.id]
    # A: 3/4 * 5 = 3.75; B: 1/4 * 5 = 1.25
    assert abs(boosts[video_a.id] - 3.75) < 0.01
    assert abs(boosts[video_b.id] - 1.25) < 0.01

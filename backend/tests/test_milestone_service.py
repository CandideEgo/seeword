"""Tests for milestone_service (Sprint 4 — E4 掌握度可视化 + 成就系统).

Covers:
- Milestone rule triggering (vocab_50, streak_7, etc.)
- No duplicate awards
- Mastery snapshot once-per-day
- API endpoints: /plan/mastery-trend, /plan/milestones
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.models.learning import Vocabulary
from app.models.learning_plan import LearningEvent, UserLearningProfile
from app.models.milestone import MasterySnapshot, UserMilestone
from app.models.user import RoleType, User
from app.services.milestone_service import (
    check_and_award,
    ensure_today_snapshot,
)

from .conftest import TestSessionLocal

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(db, phone: str = "13800000001") -> str:
    """Create a test user and return user_id."""
    user = User(
        phone=phone,
        hashed_password=hash_password("Testpass123!"),
        name="Milestone Tester",
        role=RoleType.user,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user.id


async def _create_profile(db, user_id: str, streak: int = 0) -> None:
    """Create a learning profile for the user."""
    profile = UserLearningProfile(
        user_id=user_id,
        current_streak=streak,
        longest_streak=streak,
        mastery_by_level={"new": {"count": 0}, "learning": {"count": 0}, "mastered": {"count": 0}},
    )
    db.add(profile)
    await db.commit()


async def _add_vocab(db, user_id: str, count: int, mastery_level: str = "new") -> None:
    """Add N vocabulary entries for a user."""
    for i in range(count):
        v = Vocabulary(
            user_id=user_id,
            word=f"word_{uuid.uuid4().hex[:8]}_{i}",
            mastery_level=mastery_level,
        )
        db.add(v)
    await db.commit()


async def _add_learning_events(db, user_id: str, event_type: str, count: int) -> None:
    """Add N learning events of a given type."""
    today = date.today()
    for _ in range(count):
        e = LearningEvent(
            user_id=user_id,
            event_type=event_type,
            event_value=1,
            event_date=today,
        )
        db.add(e)
    await db.commit()


@pytest.mark.asyncio
async def test_activity_no_longer_awards_milestones_or_removes_history():
    async with TestSessionLocal() as db:
        user_id = await _create_user(db)
        await _create_profile(db, user_id, streak=30)
        await _add_vocab(db, user_id, 200, mastery_level="mastered")
        old = UserMilestone(user_id=user_id, milestone_type="vocab_50")
        db.add(old)
        await db.commit()
        assert await check_and_award(db, user_id) == []
        await db.commit()
        rows = (await db.execute(select(UserMilestone).where(UserMilestone.user_id == user_id))).scalars().all()
        assert len(rows) == 1
        assert rows[0].milestone_type == "vocab_50"


# ---------------------------------------------------------------------------
# Mastery snapshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mastery_snapshot_once_per_day():
    """ensure_today_snapshot only writes one snapshot per day."""
    async with TestSessionLocal() as db:
        user_id = await _create_user(db, phone="13800000010")
        await _create_profile(db, user_id)
        today = date.today()
        mastery = {"new": {"count": 5}, "learning": {"count": 3}, "mastered": {"count": 1}}

        # First call — writes snapshot
        await ensure_today_snapshot(db, user_id, today, mastery)
        await db.commit()

        # Second call — should NOT write another
        await ensure_today_snapshot(db, user_id, today, mastery)
        await db.commit()

        result = await db.execute(
            select(MasterySnapshot).where(
                MasterySnapshot.user_id == user_id,
                MasterySnapshot.snapshot_date == today,
            )
        )
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].mastery_json == mastery


@pytest.mark.asyncio
async def test_mastery_snapshot_different_days():
    """Snapshots on different days are separate records."""
    async with TestSessionLocal() as db:
        user_id = await _create_user(db, phone="13800000011")
        await _create_profile(db, user_id)
        today = date.today()
        yesterday = today - timedelta(days=1)
        mastery = {"new": {"count": 10}}

        await ensure_today_snapshot(db, user_id, yesterday, mastery)
        await ensure_today_snapshot(db, user_id, today, mastery)
        await db.commit()

        result = await db.execute(select(MasterySnapshot).where(MasterySnapshot.user_id == user_id))
        rows = result.scalars().all()
        assert len(rows) == 2


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mastery_trend_api(client: AsyncClient, auth_headers: dict):
    """GET /api/v1/plan/mastery-trend returns snapshots."""
    # Get user_id from token
    from app.core.security import decode_token

    token = auth_headers["Authorization"].split(" ")[1]
    user_id = decode_token(token)["sub"]

    # Insert snapshots directly
    async with TestSessionLocal() as db:
        today = date.today()
        for i in range(3):
            snap = MasterySnapshot(
                user_id=user_id,
                snapshot_date=today - timedelta(days=i),
                mastery_json={"new": {"count": i * 5}},
            )
            db.add(snap)
        await db.commit()

    resp = await client.get("/api/v1/plan/mastery-trend?weeks=4", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshots" in data
    assert len(data["snapshots"]) == 3
    # Should be ordered by date ascending
    dates = [s["date"] for s in data["snapshots"]]
    assert dates == sorted(dates)


@pytest.mark.asyncio
async def test_milestones_api(client: AsyncClient, auth_headers: dict):
    """GET /api/v1/plan/milestones returns user milestones."""
    from app.core.security import decode_token

    token = auth_headers["Authorization"].split(" ")[1]
    user_id = decode_token(token)["sub"]

    # Insert a milestone
    async with TestSessionLocal() as db:
        m = UserMilestone(
            user_id=user_id,
            milestone_type="vocab_50",
            metadata_json={"word_count": 50},
        )
        db.add(m)
        await db.commit()

    resp = await client.get("/api/v1/plan/milestones", headers=auth_headers)
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_profile_includes_milestones(client: AsyncClient, auth_headers: dict):
    """GET /api/v1/plan/profile includes milestones field."""
    from app.core.security import decode_token

    token = auth_headers["Authorization"].split(" ")[1]
    user_id = decode_token(token)["sub"]

    # Create profile + milestone
    async with TestSessionLocal() as db:
        profile = UserLearningProfile(
            user_id=user_id,
            current_streak=3,
            longest_streak=5,
        )
        db.add(profile)
        m = UserMilestone(
            user_id=user_id,
            milestone_type="first_review",
        )
        db.add(m)
        await db.commit()

    resp = await client.get("/api/v1/plan/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "milestones" in data
    assert data["milestones"] == []

"""Tests for build_vocabulary_drill exam-level filtering.

The vocabulary drill previously accepted ``target_level`` but never used it —
every level saw the same words. These tests verify ECDICT-backed level
filtering now runs, with a fallback so practice still works when too few words
match the target level.
"""

import pytest

from app.models.learning import Vocabulary
from app.models.user import RoleType, User
from app.services import ecdict, practice_service
from tests.conftest import TestSessionLocal, hash_password


def _vocab_rows(user_id: str) -> list[Vocabulary]:
    # 6 cet4 words + 6 cet6 words. translations populated so the "enriched"
    # preference doesn't reorder them — level filtering is what we're testing.
    rows = []
    for w in ("apple", "banana", "cherry", "river", "mountain", "forest"):
        rows.append(Vocabulary(user_id=user_id, word=w, translation=f"释义{w}", definition="a cet4 word"))
    for w in ("abstract", "concept", "hypothesis", "paradigm", "synthesis", "empirical"):
        rows.append(Vocabulary(user_id=user_id, word=w, translation=f"释义{w}", definition="a cet6 word"))
    return rows


def _fake_lookup(token: str):
    """cet4 words → ['cet4']; cet6 words → ['cet6']; else None."""
    cet4 = {"apple", "banana", "cherry", "river", "mountain", "forest"}
    cet6 = {"abstract", "concept", "hypothesis", "paradigm", "synthesis", "empirical"}
    t = token.lower()
    if t in cet4:
        return {"lemma": token, "levels": ["cet4"]}
    if t in cet6:
        return {"lemma": token, "levels": ["cet6"]}
    return None


@pytest.mark.asyncio
async def test_vocabulary_drill_filters_by_target_level(fake_redis, monkeypatch):
    """target_level=cet6 with enough cet6 matches should return ONLY cet6 words."""
    monkeypatch.setattr(ecdict, "is_available", lambda: True)
    monkeypatch.setattr(ecdict, "lookup", _fake_lookup)

    async with TestSessionLocal() as db:
        user = User(
            phone="13800138010",
            hashed_password=hash_password("Vocabpass1!"),
            name="Vocab",
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        for v in _vocab_rows(user.id):
            db.add(v)
        await db.commit()
        uid = user.id

    async with TestSessionLocal() as db:
        # count=5, matches=6 cet6 → 6 >= 5 → restrict to cet6 only.
        items = await practice_service.build_vocabulary_drill(db, uid, target_level="cet6", count=5)

    words = {i["word"] for i in items}
    cet6 = {"abstract", "concept", "hypothesis", "paradigm", "synthesis", "empirical"}
    # All returned words must be cet6 (no cet4 leakage).
    assert words <= cet6
    assert len(words) == 5


@pytest.mark.asyncio
async def test_vocabulary_drill_falls_back_when_too_few_matches(fake_redis, monkeypatch):
    """target_level=gre matches nothing; fall back to unfiltered so practice
    still returns words rather than an empty drill."""
    monkeypatch.setattr(ecdict, "is_available", lambda: True)
    monkeypatch.setattr(ecdict, "lookup", _fake_lookup)

    async with TestSessionLocal() as db:
        user = User(
            phone="13800138011",
            hashed_password=hash_password("Vocabpass1!"),
            name="Vocab",
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        for v in _vocab_rows(user.id):
            db.add(v)
        await db.commit()
        uid = user.id

    async with TestSessionLocal() as db:
        items = await practice_service.build_vocabulary_drill(db, uid, target_level="gre", count=12)

    words = {i["word"] for i in items}
    cet4 = {"apple", "banana", "cherry", "river", "mountain", "forest"}
    cet6 = {"abstract", "concept", "hypothesis", "paradigm", "synthesis", "empirical"}
    # No gre words → matches empty → fallback returns a mix of both levels.
    assert words & cet4 and words & cet6
    assert words <= (cet4 | cet6)


@pytest.mark.asyncio
async def test_vocabulary_drill_no_level_returns_all(fake_redis, monkeypatch):
    """No target_level → no filtering, all words returned (legacy behavior)."""
    monkeypatch.setattr(ecdict, "is_available", lambda: True)
    monkeypatch.setattr(ecdict, "lookup", _fake_lookup)

    async with TestSessionLocal() as db:
        user = User(
            phone="13800138012",
            hashed_password=hash_password("Vocabpass1!"),
            name="Vocab",
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        for v in _vocab_rows(user.id):
            db.add(v)
        await db.commit()
        uid = user.id

    async with TestSessionLocal() as db:
        items = await practice_service.build_vocabulary_drill(db, uid, target_level=None, count=12)

    cet4 = {"apple", "banana", "cherry", "river", "mountain", "forest"}
    cet6 = {"abstract", "concept", "hypothesis", "paradigm", "synthesis", "empirical"}
    assert {i["word"] for i in items} == cet4 | cet6

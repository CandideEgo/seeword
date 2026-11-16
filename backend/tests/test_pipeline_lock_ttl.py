"""Pipeline lock TTL and translating-step watchdog timing (BE-12).

The processing lock used to be a fixed 60 minutes while the watchdog budgets of
the steps it protects add up to more than 150 minutes, so a long legitimate run
could lose its lock and let a duplicate trigger run the same steps. The TTL now
covers the declared budgets and is refreshed at every step boundary;
``_run_translating`` also stamps ``step_started_at`` before the LLM work rather
than after it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.tasks.pipeline_helpers as ph
import app.tasks.video_processing as vp


def test_lock_ttl_covers_all_declared_step_budgets():
    budgets = ph.get_step_timeouts()
    assert budgets, "STEPS must declare watchdog budgets"
    # 10-minute cushion plus a 60-minute floor, per lock_ttl_seconds().
    assert ph.lock_ttl_seconds() >= sum(budgets.values()) + 10 * 60


def test_lock_ttl_has_a_floor_for_tiny_budgets(monkeypatch):
    monkeypatch.setattr(ph, "get_step_timeouts", lambda: {"translating": 60})
    assert ph.lock_ttl_seconds() == 60 * 60


def test_refresh_lock_extends_an_existing_lock(monkeypatch):
    calls: list[tuple[str, int]] = []

    class _Redis:
        def expire(self, key: str, ttl: int) -> None:
            calls.append((key, ttl))

    monkeypatch.setattr(ph, "get_pipeline_redis", lambda: _Redis())
    ph.refresh_lock("video-1")
    assert calls == [("video:processing:video-1", ph.lock_ttl_seconds())]


def test_refresh_lock_failure_is_best_effort(monkeypatch):
    def _boom():
        raise RuntimeError("redis down")

    monkeypatch.setattr(ph, "get_pipeline_redis", _boom)
    # Must not raise: lock refresh is a liveness optimization, not a gate.
    ph.refresh_lock("video-2")


class _FakeResult:
    def __init__(self, rows: list) -> None:
        self._rows = rows

    def scalars(self):
        return SimpleNamespace(all=lambda: self._rows)


class _FakeDB:
    def __init__(self, rows: list) -> None:
        self._rows = rows
        self.commits = 0

    async def execute(self, _stmt):
        return _FakeResult(self._rows)

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_translating_stamps_step_started_at_before_llm_work(monkeypatch):
    subtitle = SimpleNamespace(text_en="Hello", text_zh=None)
    seen_started_at: list[object] = []

    async def fake_translate(texts, *, video_id, engine):
        seen_started_at.append(ctx.video.step_started_at)
        return ["你好"], None

    async def fake_update_progress(video_id, step):
        return None

    monkeypatch.setattr(vp, "_translate_subtitles", fake_translate)
    monkeypatch.setattr(vp, "update_progress", fake_update_progress)

    ctx = ph.PipelineCtx(
        db=_FakeDB([subtitle]),
        video=SimpleNamespace(
            id="video-3",
            title_zh="标题",
            processing_step=None,
            processing_progress=None,
            step_started_at=None,
        ),
        video_id="video-3",
        engine=None,
    )

    await vp._run_translating(ctx)

    # The watchdog was reading the previous step's timestamp until translation
    # finished; it must now see a fresh start before _translate_subtitles runs.
    assert seen_started_at and seen_started_at[0] is not None
    assert ctx.video.processing_step == "translating"
    assert ctx.video.step_started_at is not None
    assert ctx.db.commits >= 2

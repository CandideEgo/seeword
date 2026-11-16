"""回归测试：管理面字幕/管线数据安全（ADM-01/02/03/04/10/12/14/18）。

覆盖本轮修复的「副作用」，不只断言状态码：

- ``retranslate``：状态守卫（processing/ready_subtitles/pending_processing →
  409，且不清空译文）、engine 白名单（非法 → 422）、Redis 单飞锁；broker 失败
  保留已提交的重译状态和 pending outbox，补发使用同一 generation 与 engine。
- ``recover``/``retry``：活锁（步骤预算内）→ 409 且**不删锁**、不派发；陈旧运行
  以新 generation 隔离；60s 单飞键挡住连点，有字幕走 tail、无字幕 recover 走 head。
- ``/videos/seed``：去重覆盖 pending_processing/processing/ready_subtitles/ready；
  URL 级 Redis 锁；连点只建一行、只派发一次；error 仍允许重试；broker 失败返回
  成功并保留 pending outbox；数据库提交失败则状态和意图一起 rollback。
- 单行删除字幕：默认 409 + 影响计数，``?force=true`` 才级联删除，且显式清理
  favorites/revisions、把 vocabulary 来源句置空（与 Postgres 级联一致）。
- ``create_subtitle`` 的 max+1 分配走视频行 ``FOR UPDATE``。
- schema 长字段校验（title/title_zh/topic_tags 500、reject reason 1000）→ 422；
  管理状态接口的 ``error_message`` 截断到 500；revisions 列表返回 ``total``。
"""

import asyncio
import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core import redis as redis_module
from app.models.learning import Vocabulary
from app.models.pipeline_dispatch import DISPATCH_STATUS_DISPATCHED, DISPATCH_STATUS_PENDING, PipelineDispatch
from app.models.subtitle import Subtitle
from app.models.subtitle_revision import SubtitleRevision
from app.models.user import User
from app.models.user_content import SentenceFavorite
from app.models.video import Video, VideoStatus
from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK, PROCESS_VIDEO_TASK, dispatch_pending
from app.services.processing_generation import run_identity
from tests.conftest import TestSessionLocal, _FakeRedis

# ---------------------------------------------------------------------------
# helpers / fixtures
# ---------------------------------------------------------------------------


class _NxRedis(_FakeRedis):
    """套件里的 ``_FakeRedis`` + 真 ``SET NX EX`` 语义。

    ``conftest._FakeRedis.set`` 只接受 ``ex``（它是给缓存/冷却逻辑用的），
    而本轮新增的单飞/URL 锁依赖 ``nx=True``。生产代码按真 Redis 语义写
    ``set(key, "1", nx=True, ex=ttl)``，所以测试侧要有同样语义的替身——
    与 ``test_internal_callback.py`` 的 ``_FakeAsyncRedis`` 是同一模式。
    """

    async def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> str | None:
        self._purge(key)
        if nx and key in self._store:
            return None
        self._store[key] = value
        if ex is not None:
            self._expires[key] = time.monotonic() + ex
        else:
            self._expires.pop(key, None)
        return "OK"


@pytest.fixture
def nx_redis(monkeypatch) -> _NxRedis:
    """把 ``app.core.redis.get_redis`` 换成支持 SET NX 的内存替身。

    服务层在函数调用时 ``from app.core.redis import get_redis``，所以改模块属性
    就能覆盖到；这里比 conftest 的 autouse 替身晚生效，只影响本测试。
    """
    fake = _NxRedis()
    monkeypatch.setattr(redis_module, "get_redis", lambda: fake)
    return fake


async def _create_video(
    *,
    status: VideoStatus = VideoStatus.ready,
    url: str | None = None,
    title: str = "Admin fix test",
    error_message: str | None = None,
    quality_flag: str | None = None,
    processing_step: str | None = None,
    step_started_at: datetime | None = None,
    processing_started_at: datetime | None = None,
) -> str:
    async with TestSessionLocal() as db:
        video = Video(
            title=title,
            source_url=url or f"https://youtu.be/{uuid.uuid4().hex[:11]}",
            video_source="imported",
            status=status,
            is_official=True,
            is_published=False,
            error_message=error_message,
            quality_flag=quality_flag,
            processing_step=processing_step,
            step_started_at=step_started_at,
            processing_started_at=processing_started_at,
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video.id


async def _add_subtitles(video_id: str, count: int = 2, *, with_zh: bool = True) -> list[str]:
    async with TestSessionLocal() as db:
        rows = [
            Subtitle(
                video_id=video_id,
                start_time=float(i),
                end_time=float(i + 1),
                text_en=f"line {i}",
                text_zh=(f"旧翻译 {i}" if with_zh else None),
                sentence_index=i,
            )
            for i in range(count)
        ]
        db.add_all(rows)
        await db.commit()
        return [row.id for row in rows]


async def _subtitles(video_id: str) -> list[Subtitle]:
    async with TestSessionLocal() as db:
        return list(
            (await db.execute(select(Subtitle).where(Subtitle.video_id == video_id).order_by(Subtitle.sentence_index)))
            .scalars()
            .all()
        )


async def _video(video_id: str) -> Video:
    async with TestSessionLocal() as db:
        return (await db.execute(select(Video).where(Video.id == video_id))).scalar_one()


async def _count_videos(url: str) -> int:
    async with TestSessionLocal() as db:
        return (await db.scalar(select(func.count()).select_from(Video).where(Video.source_url == url))) or 0


async def _dispatches(video_id: str) -> list[PipelineDispatch]:
    async with TestSessionLocal() as db:
        return list((await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == video_id))).all())


async def _assert_dispatch(
    video_id: str,
    task_name: str,
    *,
    engine: str | None = None,
    status: str = DISPATCH_STATUS_DISPATCHED,
) -> PipelineDispatch:
    (row,) = await _dispatches(video_id)
    video = await _video(video_id)
    assert video.processing_generation
    assert row.processing_generation == video.processing_generation
    assert row.task_name == task_name
    assert row.queue is None
    expected_args = [video_id, engine] if task_name == FINALIZE_VIDEO_TASK else [video_id]
    assert row.args == [*expected_args, video.processing_generation]
    assert row.status == status
    assert row.attempts == 1
    if status == DISPATCH_STATUS_PENDING:
        assert row.last_error == "broker down"
        assert row.next_attempt_at is not None
        assert row.dispatched_at is None
    else:
        assert row.last_error is None
        assert row.next_attempt_at is None
        assert row.dispatched_at is not None
    return row


async def _assert_pending_can_resend(row: PipelineDispatch) -> None:
    """模拟 beat 在 backoff 到期补发，不能产生另一行或换代。"""
    assert row.next_attempt_at is not None
    due = row.next_attempt_at.replace(tzinfo=UTC) + timedelta(seconds=1)
    with (
        patch("app.services.pipeline_dispatch._utcnow", return_value=due),
        patch("app.services.pipeline_dispatch._send_task") as send,
    ):
        async with TestSessionLocal() as db:
            sweep = await dispatch_pending(db)
    assert sweep.scanned == sweep.sent == 1
    assert sweep.failed == sweep.abandoned == 0
    send.assert_called_once_with(row.task_name, row.args, row.queue)
    (fresh,) = await _dispatches(row.video_id)
    assert fresh.id == row.id
    assert fresh.args == row.args
    assert fresh.processing_generation == row.processing_generation
    assert fresh.status == DISPATCH_STATUS_DISPATCHED
    assert fresh.attempts == 2
    assert fresh.last_error is None
    assert fresh.next_attempt_at is None
    assert fresh.dispatched_at is not None


async def _user_id(phone: str = "13800138000") -> str:
    async with TestSessionLocal() as db:
        return (await db.execute(select(User).where(User.phone == phone))).scalar_one().id


# ---------------------------------------------------------------------------
# ADM-02: retranslate 状态守卫 / engine 白名单 / 单飞 / 持久重译意图
# ---------------------------------------------------------------------------


class TestRetranslateGuards:
    @pytest.mark.parametrize(
        "status",
        [VideoStatus.processing, VideoStatus.ready_subtitles, VideoStatus.pending_processing],
    )
    async def test_rejects_video_mid_pipeline(self, client: AsyncClient, admin_headers: dict, status: VideoStatus):
        vid = await _create_video(status=status)
        await _add_subtitles(vid, 2)

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate", headers=admin_headers)

        assert resp.status_code == 409, resp.text
        assert resp.json()["code"] == "CONFLICT"
        mock_fin.assert_not_called()
        # 守卫必须先于清空：译文原样保留。
        rows = await _subtitles(vid)
        assert [row.text_zh for row in rows] == ["旧翻译 0", "旧翻译 1"]
        assert (await _video(vid)).status == status

    async def test_unknown_engine_is_422(self, client: AsyncClient, admin_headers: dict):
        vid = await _create_video(status=VideoStatus.error, quality_flag="quality_blocked")
        await _add_subtitles(vid, 1)

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate?engine=bogus", headers=admin_headers)

        assert resp.status_code == 422, resp.text
        assert resp.json()["code"] == "VALIDATION_ERROR"
        mock_fin.assert_not_called()
        assert (await _subtitles(vid))[0].text_zh == "旧翻译 0"

    async def test_dispatch_failure_keeps_new_translation_intent(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis
    ):
        """broker 失败不补偿旧译文；新重译意图已持久化，可由 beat 补发。"""
        vid = await _create_video(
            status=VideoStatus.error,
            quality_flag="quality_blocked",
            error_message="coverage 50% below block",
            processing_step=None,
        )
        subtitle_ids = await _add_subtitles(vid, 3)
        previous_generation = (await _video(vid)).processing_generation

        with patch("app.services.pipeline_dispatch._send_task", side_effect=RuntimeError("broker down")) as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate?engine=glm", headers=admin_headers)
            repeated = await client.post(f"/api/v1/videos/admin/{vid}/retranslate?engine=glm", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        assert repeated.status_code == 409, repeated.text
        assert nx_redis._store.get(f"retranslate:{vid}") == "1"
        rows = await _subtitles(vid)
        assert [row.id for row in rows] == subtitle_ids
        assert [row.text_en for row in rows] == ["line 0", "line 1", "line 2"]
        assert [row.text_zh for row in rows] == [None, None, None]
        fresh = await _video(vid)
        assert fresh.status == VideoStatus.ready_subtitles
        assert fresh.quality_flag is None
        assert fresh.error_message is None
        assert fresh.processing_step == "translating"
        assert fresh.processing_generation != previous_generation
        row = await _assert_dispatch(vid, FINALIZE_VIDEO_TASK, engine="glm", status=DISPATCH_STATUS_PENDING)
        send.assert_called_once_with(FINALIZE_VIDEO_TASK, row.args, None)
        await _assert_pending_can_resend(row)
        assert [row.text_zh for row in await _subtitles(vid)] == [None, None, None]

    async def test_single_flight_lock_blocks_double_click(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis
    ):
        vid = await _create_video(status=VideoStatus.error, quality_flag="quality_blocked")
        await _add_subtitles(vid, 1)
        nx_redis._store[f"retranslate:{vid}"] = "1"

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate", headers=admin_headers)

        assert resp.status_code == 409, resp.text
        assert "重新翻译" in resp.json()["message"]
        mock_fin.assert_not_called()
        assert (await _subtitles(vid))[0].text_zh == "旧翻译 0"

    async def test_successful_call_takes_single_flight_key(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis
    ):
        vid = await _create_video(status=VideoStatus.error, quality_flag="quality_blocked")
        await _add_subtitles(vid, 1)

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        row = await _assert_dispatch(vid, FINALIZE_VIDEO_TASK)
        mock_fin.assert_called_once_with(FINALIZE_VIDEO_TASK, row.args, None)
        assert nx_redis._store.get(f"retranslate:{vid}") == "1"
        # 清空 + 状态推进仍然生效（成功路径）。
        assert (await _subtitles(vid))[0].text_zh is None
        assert (await _video(vid)).status == VideoStatus.ready_subtitles


# ---------------------------------------------------------------------------
# ADM-03: recover / retry 不杀活锁 + 60s 单飞
# ---------------------------------------------------------------------------


class TestRecoverRetryLockSafety:
    async def test_recover_rejects_live_lock_and_keeps_it(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis
    ):
        vid = await _create_video(
            status=VideoStatus.ready_subtitles,
            processing_step="translating",
            step_started_at=datetime.now(UTC) - timedelta(seconds=30),
        )
        nx_redis._store[f"video:processing:{vid}"] = "1"

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/recover", headers=admin_headers)

        assert resp.status_code == 409, resp.text
        assert resp.json()["code"] == "CONFLICT"
        assert "translating" in resp.json()["message"]
        # 活锁不能被删（否则第二个 finalize 会并发写同一批字幕行）。
        assert nx_redis._store.get(f"video:processing:{vid}") == "1"
        mock_fin.assert_not_called()

    @pytest.mark.parametrize("with_subtitles", [False, True])
    async def test_recover_fences_stale_lock_and_dispatches(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis, with_subtitles: bool
    ):
        vid = await _create_video(
            status=VideoStatus.ready_subtitles,
            processing_step="translating",
            step_started_at=datetime.now(UTC) - timedelta(days=2),
        )
        subtitle_ids = await _add_subtitles(vid) if with_subtitles else []
        previous = await _video(vid)
        stale_lock = f"video:processing:{run_identity(vid, previous.processing_generation)}"
        nx_redis._store[stale_lock] = "1"

        with patch("app.services.pipeline_dispatch._send_task") as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/recover", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        task_name = FINALIZE_VIDEO_TASK if with_subtitles else PROCESS_VIDEO_TASK
        row = await _assert_dispatch(vid, task_name)
        send.assert_called_once_with(task_name, row.args, None)
        fresh = await _video(vid)
        assert fresh.processing_generation != previous.processing_generation
        assert fresh.status == (VideoStatus.ready_subtitles if with_subtitles else VideoStatus.processing)
        assert fresh.processing_step == ("translating" if with_subtitles else "extracting")
        assert fresh.processing_progress == (70 if with_subtitles else 0)
        assert fresh.error_message is None
        # 不删除另一个运行的锁；新代与旧代隔离。
        assert nx_redis._store.get(stale_lock) == "1"
        assert f"video:processing:{run_identity(vid, fresh.processing_generation)}" not in nx_redis._store
        assert nx_redis._store.get(f"pipeline:resume:{vid}") == "1"
        assert [sub.id for sub in await _subtitles(vid)] == subtitle_ids
        if with_subtitles:
            assert [sub.text_zh for sub in await _subtitles(vid)] == ["旧翻译 0", "旧翻译 1"]

    async def test_recover_double_click_single_flight(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis
    ):
        vid = await _create_video(
            status=VideoStatus.ready_subtitles,
            processing_step="translating",
            step_started_at=datetime.now(UTC) - timedelta(days=1),
        )

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            first = await client.post(f"/api/v1/videos/admin/{vid}/recover", headers=admin_headers)
            second = await client.post(f"/api/v1/videos/admin/{vid}/recover", headers=admin_headers)

        assert first.status_code == 200, first.text
        assert second.status_code == 409, second.text
        assert "60 秒" in second.json()["message"]
        assert mock_fin.call_count == 1
        row = await _assert_dispatch(vid, PROCESS_VIDEO_TASK)
        mock_fin.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)

    @pytest.mark.parametrize("with_subtitles", [False, True])
    async def test_recover_dispatch_failure_keeps_pending_intent(
        self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis, with_subtitles: bool
    ):
        vid = await _create_video(
            status=VideoStatus.ready_subtitles,
            processing_step="translating",
            step_started_at=datetime.now(UTC) - timedelta(days=1),
        )
        if with_subtitles:
            await _add_subtitles(vid)

        with patch("app.services.pipeline_dispatch._send_task", side_effect=RuntimeError("broker down")) as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/recover", headers=admin_headers)
            repeated = await client.post(f"/api/v1/videos/admin/{vid}/recover", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        assert repeated.status_code == 409, repeated.text
        assert "60 秒" in repeated.json()["message"]
        assert nx_redis._store.get(f"pipeline:resume:{vid}") == "1"
        task_name = FINALIZE_VIDEO_TASK if with_subtitles else PROCESS_VIDEO_TASK
        row = await _assert_dispatch(vid, task_name, status=DISPATCH_STATUS_PENDING)
        send.assert_called_once_with(task_name, row.args, None)
        await _assert_pending_can_resend(row)
        assert [sub.text_zh for sub in await _subtitles(vid)] == (["旧翻译 0", "旧翻译 1"] if with_subtitles else [])

    async def test_retry_rejects_live_lock(self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis):
        vid = await _create_video(
            status=VideoStatus.error,
            processing_started_at=datetime.now(UTC) - timedelta(seconds=5),
        )
        nx_redis._store[f"video:processing:{vid}"] = "1"

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)

        assert resp.status_code == 409, resp.text
        assert nx_redis._store.get(f"video:processing:{vid}") == "1"
        mock_fin.assert_not_called()

    async def test_retry_stale_lock_proceeds(self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis):
        vid = await _create_video(
            status=VideoStatus.error,
            processing_step="translating",
            step_started_at=datetime.now(UTC) - timedelta(days=1),
        )
        await _add_subtitles(vid, 1)
        nx_redis._store[f"video:processing:{vid}"] = "1"

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        row = await _assert_dispatch(vid, FINALIZE_VIDEO_TASK)
        mock_fin.assert_called_once_with(FINALIZE_VIDEO_TASK, row.args, None)
        # 旧锁仍归旧运行所有；重试已生成新的隔离身份。
        fresh = await _video(vid)
        assert fresh.processing_generation
        assert nx_redis._store.get(f"video:processing:{vid}") == "1"
        assert f"video:processing:{run_identity(vid, fresh.processing_generation)}" not in nx_redis._store
        assert (await _subtitles(vid))[0].text_zh == "旧翻译 0"


# ---------------------------------------------------------------------------
# ADM-04: /videos/seed 去重 + URL 级锁
# ---------------------------------------------------------------------------


class TestSeedDedupeAndLock:
    @pytest.mark.parametrize(
        "status",
        [
            VideoStatus.pending_processing,
            VideoStatus.processing,
            VideoStatus.ready_subtitles,
            VideoStatus.ready,
        ],
    )
    async def test_reclick_reuses_existing_row(self, client: AsyncClient, admin_headers: dict, status: VideoStatus):
        url = f"https://youtu.be/dedupe-{status.value}-{uuid.uuid4().hex[:6]}"
        existing_id = await _create_video(status=status, url=url)

        with patch("app.services.pipeline_dispatch._send_task") as mock_pv:
            resp = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)

        assert resp.status_code == 201, resp.text
        assert resp.json()["id"] == existing_id
        mock_pv.assert_not_called()
        assert await _count_videos(url) == 1

    async def test_error_video_still_retryable(self, client: AsyncClient, admin_headers: dict):
        url = f"https://youtu.be/error-retry-{uuid.uuid4().hex[:6]}"
        errored_id = await _create_video(status=VideoStatus.error, url=url)

        with patch("app.services.pipeline_dispatch._send_task") as mock_pv:
            resp = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)

        assert resp.status_code == 201, resp.text
        new_id = resp.json()["id"]
        assert new_id != errored_id
        row = await _assert_dispatch(new_id, PROCESS_VIDEO_TASK)
        mock_pv.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)
        assert await _count_videos(url) == 2
        assert await _dispatches(errored_id) == []

    async def test_url_lock_conflict_is_409(self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis):
        from app.services.video_seed_service import _seed_lock_key

        url = f"https://youtu.be/locked-{uuid.uuid4().hex[:6]}"
        nx_redis._store[_seed_lock_key(url)] = "1"

        with patch("app.services.pipeline_dispatch._send_task") as mock_pv:
            resp = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)

        assert resp.status_code == 409, resp.text
        assert resp.json()["code"] == "CONFLICT"
        mock_pv.assert_not_called()
        assert await _count_videos(url) == 0

    async def test_double_click_creates_one_row(self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis):
        url = f"https://youtu.be/double-click-{uuid.uuid4().hex[:6]}"

        with patch("app.services.pipeline_dispatch._send_task") as mock_pv:
            first = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)
            second = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)

        assert first.status_code == 201, first.text
        assert second.status_code == 201, second.text
        assert first.json()["id"] == second.json()["id"]
        assert mock_pv.call_count == 1
        assert await _count_videos(url) == 1
        async with TestSessionLocal() as db:
            vid = (await db.scalars(select(Video.id).where(Video.source_url == url))).one()
        row = await _assert_dispatch(vid, PROCESS_VIDEO_TASK)
        mock_pv.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)

    async def test_concurrent_seed_creates_one_row(self, client: AsyncClient, admin_headers: dict, nx_redis: _NxRedis):
        """并发两击：要么第二个 409（锁生效），要么命中去重返回同一行；只建一行。"""
        url = f"https://youtu.be/concurrent-{uuid.uuid4().hex[:6]}"

        with patch("app.services.pipeline_dispatch._send_task") as mock_pv:
            responses = await asyncio.gather(
                client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers),
                client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers),
            )

        statuses = sorted(resp.status_code for resp in responses)
        assert statuses in ([201, 201], [201, 409]), [resp.text for resp in responses]
        assert await _count_videos(url) == 1
        assert mock_pv.call_count == 1
        vid = next(resp.json()["id"] for resp in responses if resp.status_code == 201)
        row = await _assert_dispatch(vid, PROCESS_VIDEO_TASK)
        mock_pv.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)

    async def test_dispatch_failure_keeps_pending_head(self, client: AsyncClient, admin_headers: dict):
        """broker 失败仍创建成功，head 意图已持久化且可补发。"""
        url = f"https://youtu.be/dispatch-fail-{uuid.uuid4().hex[:6]}"

        with patch("app.services.pipeline_dispatch._send_task", side_effect=RuntimeError("broker down")) as send:
            resp = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)
            repeated = await client.post("/api/v1/videos/seed", json={"source_url": url}, headers=admin_headers)

        assert resp.status_code == 201, resp.text
        assert repeated.status_code == 201, repeated.text
        vid = resp.json()["id"]
        assert repeated.json()["id"] == vid
        assert await _count_videos(url) == 1
        video = await _video(vid)
        assert video.status == VideoStatus.processing
        assert video.processing_step == "extracting"
        assert video.error_message is None
        row = await _assert_dispatch(vid, PROCESS_VIDEO_TASK, status=DISPATCH_STATUS_PENDING)
        send.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)
        await _assert_pending_can_resend(row)


class TestAdminPipelineTransactions:
    @pytest.mark.parametrize("action", ["seed", "retranslate", "recover", "retry"])
    async def test_commit_failure_rolls_back_state_subtitles_and_outbox(self, action: str):
        """真实 enqueue 已写 SQLite，commit 失败必须一起 rollback，且不碰 broker。"""
        from app.services import video_seed_service

        url = f"https://youtu.be/rollback-{uuid.uuid4().hex[:6]}"
        vid = None
        before = None
        subtitle_ids = []
        if action != "seed":
            vid = await _create_video(
                status=VideoStatus.processing if action == "recover" else VideoStatus.error,
                quality_flag="quality_blocked",
                error_message="original failure",
                processing_step="translating",
                step_started_at=datetime.now(UTC) - timedelta(days=1),
            )
            subtitle_ids = await _add_subtitles(vid)
            before = await _video(vid)

        async with TestSessionLocal() as db:
            with (
                patch.object(db, "commit", new=AsyncMock(side_effect=SQLAlchemyError("commit failed"))),
                patch.object(db, "rollback", wraps=db.rollback) as rollback,
                patch("app.services.pipeline_dispatch._send_task") as send,
            ):
                with pytest.raises(SQLAlchemyError, match="commit failed"):
                    if action == "seed":
                        await video_seed_service.seed_video(db, url)
                    elif action == "retranslate":
                        await video_seed_service.retranslate_video(db, vid, engine="glm")
                    elif action == "recover":
                        await video_seed_service.recover_processing(db, vid)
                    else:
                        await video_seed_service.retry_video(db, vid)
                rollback.assert_awaited_once()
                send.assert_not_called()

        async with TestSessionLocal() as db:
            assert (await db.scalar(select(func.count()).select_from(PipelineDispatch))) == 0
        if action == "seed":
            assert await _count_videos(url) == 0
        else:
            fresh = await _video(vid)
            for field in (
                "status",
                "quality_flag",
                "error_message",
                "processing_step",
                "processing_progress",
                "processing_generation",
                "step_started_at",
            ):
                assert getattr(fresh, field) == getattr(before, field), field
            rows = await _subtitles(vid)
            assert [row.id for row in rows] == subtitle_ids
            assert [row.text_zh for row in rows] == ["旧翻译 0", "旧翻译 1"]

    @pytest.mark.parametrize("action", ["retry", "recover", "retranslate"])
    async def test_requires_admin(self, client: AsyncClient, auth_headers: dict, action: str):
        vid = await _create_video(status=VideoStatus.error)
        await _add_subtitles(vid)
        with patch("app.services.pipeline_dispatch._send_task") as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/{action}", headers=auth_headers)
        assert resp.status_code == 403, resp.text
        send.assert_not_called()
        assert await _dispatches(vid) == []
        assert (await _video(vid)).status == VideoStatus.error
        assert [row.text_zh for row in await _subtitles(vid)] == ["旧翻译 0", "旧翻译 1"]


# ---------------------------------------------------------------------------
# ADM-01 同源：单行删除字幕默认 409 + force 才级联
# ---------------------------------------------------------------------------


async def _seed_subtitle_with_user_data(
    *, with_favorites: bool = True, with_revisions: bool = True
) -> tuple[str, str, str]:
    """视频 + 1 条字幕 + 用户收藏/编辑历史/词来源句；返回 (video_id, subtitle_id, user_id)。"""
    vid = await _create_video()
    (sid,) = await _add_subtitles(vid, 1)
    uid = await _user_id()
    async with TestSessionLocal() as db:
        if with_favorites:
            db.add(SentenceFavorite(user_id=uid, subtitle_id=sid))
        if with_revisions:
            db.add(
                SubtitleRevision(
                    subtitle_id=sid,
                    video_id=vid,
                    edited_by=None,
                    scope="fork",
                    before={"text_en": "line 0"},
                    after={"text_en": "edited"},
                )
            )
        db.add(Vocabulary(user_id=uid, word="line", video_id=vid, subtitle_id=sid))
        await db.commit()
    return vid, sid, uid


class TestDeleteSubtitleGuard:
    async def test_default_delete_requires_force(self, client: AsyncClient, auth_headers: dict, admin_headers: dict):
        vid, sid, _uid = await _seed_subtitle_with_user_data()

        resp = await client.delete(f"/api/v1/videos/admin/{vid}/subtitles/{sid}", headers=admin_headers)

        assert resp.status_code == 409, resp.text
        body = resp.json()
        assert body["code"] == "CONFLICT"
        assert body["detail"]["affected_favorites"] == 1
        assert body["detail"]["affected_revisions"] == 1

        # 什么都没删：字幕、收藏、编辑历史都还在。
        async with TestSessionLocal() as db:
            assert await db.get(Subtitle, sid) is not None
            assert (await db.scalar(select(func.count()).select_from(SentenceFavorite))) == 1
            assert (await db.scalar(select(func.count()).select_from(SubtitleRevision))) == 1

    async def test_force_delete_proceeds_and_reports_counts(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        vid, sid, _uid = await _seed_subtitle_with_user_data()

        resp = await client.delete(f"/api/v1/videos/admin/{vid}/subtitles/{sid}?force=true", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["deleted_id"] == sid
        assert body["favorites_deleted"] == 1
        assert body["revisions_deleted"] == 1
        assert body["forced"] is True
        assert body["remaining_count"] == 0

        async with TestSessionLocal() as db:
            assert await db.get(Subtitle, sid) is None
            assert (await db.scalar(select(func.count()).select_from(SentenceFavorite))) == 0
            assert (await db.scalar(select(func.count()).select_from(SubtitleRevision))) == 0
            vocab = (await db.execute(select(Vocabulary))).scalars().all()
            assert [word.subtitle_id for word in vocab] == [None]

    async def test_delete_without_side_effects_needs_no_force(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        vid, _sid, _uid = await _seed_subtitle_with_user_data(with_favorites=False, with_revisions=False)
        (sub_id,) = [row.id for row in await _subtitles(vid)]

        resp = await client.delete(f"/api/v1/videos/admin/{vid}/subtitles/{sub_id}", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["favorites_deleted"] == 0
        assert body["revisions_deleted"] == 0
        assert body["forced"] is False


# ---------------------------------------------------------------------------
# ADM-14: create_subtitle 的 max+1 分配走视频行 FOR UPDATE
# ---------------------------------------------------------------------------


class _RecordingSession:
    """只记录 SQL 文本的假 session（不连库）。"""

    def __init__(self) -> None:
        self.statements: list[str] = []

    async def execute(self, stmt) -> None:
        self.statements.append(str(stmt))


class TestCreateSubtitleLock:
    async def test_lock_video_row_emits_for_update(self):
        from app.services.subtitle_edit_service import lock_video_row

        db = _RecordingSession()
        await lock_video_row(db, "video-1")

        assert len(db.statements) == 1
        assert "FOR UPDATE" in db.statements[0]
        assert "videos.id" in db.statements[0]

    async def test_create_subtitle_takes_row_lock(self, client: AsyncClient, admin_headers: dict):
        from app.services import subtitle_edit_service

        vid = await _create_video()
        await _add_subtitles(vid, 1)

        with patch.object(subtitle_edit_service, "lock_video_row", new=AsyncMock()) as mock_lock:
            resp = await client.post(
                f"/api/v1/videos/admin/{vid}/subtitles",
                headers=admin_headers,
                json={"start_time": 1.0, "end_time": 2.0, "text_en": "appended"},
            )

        assert resp.status_code == 200, resp.text
        mock_lock.assert_awaited_once()
        assert mock_lock.await_args.args[1] == vid
        assert resp.json()["sentence_index"] == 1


# ---------------------------------------------------------------------------
# ADM-12 / ADM-18: schema 校验与截断
# ---------------------------------------------------------------------------


class TestSchemaLimits:
    async def test_title_over_500_is_422(self, client: AsyncClient, admin_headers: dict):
        vid = await _create_video(title="short")

        resp = await client.patch(f"/api/v1/videos/admin/{vid}", headers=admin_headers, json={"title": "x" * 501})

        assert resp.status_code == 422, resp.text
        assert resp.json()["code"] == "VALIDATION_ERROR"
        assert (await _video(vid)).title == "short"

    async def test_title_zh_and_topic_tags_over_500_are_422(self, client: AsyncClient, admin_headers: dict):
        vid = await _create_video()
        for payload in ({"title_zh": "中" * 501}, {"topic_tags": "tag," * 200}):
            resp = await client.patch(f"/api/v1/videos/admin/{vid}", headers=admin_headers, json=payload)
            assert resp.status_code == 422, (payload, resp.text)

    async def test_reject_reason_over_1000_is_422(self, client: AsyncClient, admin_headers: dict):
        vid = await _create_video()

        resp = await client.post(
            f"/api/v1/videos/admin/{vid}/review/reject",
            headers=admin_headers,
            json={"reason": "x" * 1001},
        )

        assert resp.status_code == 422, resp.text

    async def test_admin_status_truncates_error_message(self, client: AsyncClient, admin_headers: dict):
        long_message = "E" * 800
        vid = await _create_video(status=VideoStatus.error, error_message=long_message)

        resp = await client.get(f"/api/v1/videos/admin/{vid}/status", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        assert len(resp.json()["error_message"]) == 500
        # 库里仍保留完整文本供排障。
        assert len((await _video(vid)).error_message or "") == 800


# ---------------------------------------------------------------------------
# ADM-10: revisions 列表返回 total
# ---------------------------------------------------------------------------


class TestRevisionListTotal:
    async def test_revisions_include_total(self, client: AsyncClient, admin_headers: dict):
        vid = await _create_video()
        (sid,) = await _add_subtitles(vid, 1)
        for text in ("first edit", "second edit"):
            resp = await client.patch(
                f"/api/v1/videos/admin/{vid}/subtitles/{sid}",
                headers=admin_headers,
                json={"text_en": text},
            )
            assert resp.status_code == 200, resp.text

        resp = await client.get(f"/api/v1/videos/admin/{vid}/subtitles/revisions", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
        assert body["has_more"] is False

    async def test_per_subtitle_revisions_total(self, client: AsyncClient, auth_headers: dict, admin_headers: dict):
        vid = await _create_video()
        sids = await _add_subtitles(vid, 2)
        await client.patch(
            f"/api/v1/videos/admin/{vid}/subtitles/{sids[0]}",
            headers=admin_headers,
            json={"text_en": "only this one"},
        )

        resp = await client.get(f"/api/v1/videos/admin/{vid}/subtitles/{sids[1]}/revisions", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        assert resp.json()["total"] == 0
        assert resp.json()["items"] == []


# ---------------------------------------------------------------------------
# ADM-10: /videos/admin/{id}/score 从裸 dict 收成 typed 响应
# ---------------------------------------------------------------------------


class TestVideoScoreTyped:
    def test_score_response_is_typed_in_openapi(self):
        from app.main import create_app

        schema = create_app().openapi()["paths"]["/api/v1/videos/admin/{video_id}/score"]["get"]["responses"]["200"][
            "content"
        ]["application/json"]["schema"]
        assert schema["$ref"].endswith("VideoScoreResponse")

    async def test_score_payload_keeps_fields(self, client: AsyncClient, admin_headers: dict):
        from app.models.video_score import VideoScore

        vid = await _create_video()
        async with TestSessionLocal() as db:
            db.add(
                VideoScore(
                    video_id=vid,
                    total_score=42.5,
                    ctr=0.1,
                    retention=0.2,
                    watch_time=0.3,
                    topic_match=0.4,
                    quality=0.5,
                    viral=0.6,
                    freshness=0.7,
                    bonus=1.0,
                )
            )
            await db.commit()

        resp = await client.get(f"/api/v1/videos/admin/{vid}/score", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["video_id"] == vid
        assert body["total_score"] == 42.5
        assert body["factors"] == {
            "ctr": 0.1,
            "retention": 0.2,
            "watch_time": 0.3,
            "topic_match": 0.4,
            "quality": 0.5,
            "viral": 0.6,
            "freshness": 0.7,
            "bonus": 1.0,
        }
        assert body["computed_at"]

"""A12 测量口径回归：激活/留存分母、付费与试用分离、事件对账、性能 p75。

这些用例只锁**口径**，不锁实现细节：分母、成熟判定、丢失率、样本量为 0 时
返回 None——四项都是审计明确要求「写死并能回答」的东西。
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.models.behavior import BehaviorEvent
from app.models.learning_plan import LearningEvent
from app.models.pipeline_dispatch import DISPATCH_STATUS_PENDING, PipelineDispatch
from app.models.user import RoleType, User
from app.models.video import Video, VideoSource, VideoStatus
from app.services.event_contract import MEANINGFUL_EVENT_TYPES
from app.services.measurement_service import learning_metrics, percentile


def test_percentile_nearest_rank() -> None:
    assert percentile([], 0.75) is None
    assert percentile([1000], 0.75) == 1000
    values = [4000, 1000, 3000, 2000]
    # nearest-rank: ceil(0.75 * 4) = 3 -> 第 3 小的值
    assert percentile(values, 0.75) == 3000
    assert percentile(values, 0.5) == 2000


async def _user(db, phone: str, *, created_at: datetime, role=RoleType.user) -> User:
    user = User(
        phone=phone,
        name=phone,
        role=role,
        created_at=created_at,
    )
    db.add(user)
    await db.flush()
    return user


async def _event(db, user: User, event_date: date, event_type="learned_words", **kwargs) -> LearningEvent:
    event = LearningEvent(
        user_id=user.id,
        event_type=event_type,
        event_value=kwargs.pop("event_value", 1),
        event_date=event_date,
        created_at=kwargs.pop("created_at", datetime.now(UTC)),
        **kwargs,
    )
    db.add(event)
    return event


@pytest.mark.asyncio
async def test_activation_and_cohort_denominators(db_session) -> None:
    db = db_session
    now = datetime.now(UTC)
    today = now.date()
    activation_day = today - timedelta(days=2)

    activated = await _user(db, "13800000001", created_at=now - timedelta(days=2))
    late = await _user(db, "13800000002", created_at=now - timedelta(days=2))
    await _user(db, "13800000003", created_at=now - timedelta(days=2))  # silent：无学习事件
    staff = await _user(db, "13800000004", created_at=now - timedelta(days=2), role=RoleType.admin)
    await db.commit()

    # activated：注册 1 小时后首次学习，次日（D1）再次学习
    await _event(db, activated, activation_day, created_at=activated.created_at + timedelta(hours=1))
    await _event(db, activated, activation_day + timedelta(days=1))
    # late：注册 30 小时后才学习 —— 不算 24h 激活，但仍是激活日 cohort 的一员
    await _event(db, late, activation_day, created_at=late.created_at + timedelta(hours=30))
    # silent 没有学习事件；staff 是管理员，不进分母
    await _event(db, staff, activation_day, created_at=staff.created_at + timedelta(hours=1))
    await db.commit()

    metrics = await learning_metrics(db, days=7)

    activation = metrics["activation"]
    assert activation["window_registered"] == 3  # 管理员被排除
    assert activation["activated_within_24h"] == 1
    assert activation["rate"] == pytest.approx(1 / 3, abs=1e-4)

    cohort = next(c for c in metrics["cohorts"] if c["cohort_date"] == activation_day.isoformat())
    assert cohort["size"] == 2  # activated + late
    assert cohort["d1_eligible"] is True
    assert cohort["d1_retained"] == 1  # 只有 activated 在 D1 有事件
    assert cohort["d1_rate"] == pytest.approx(0.5)
    # D7 尚未成熟：不出数，也不补分母
    assert cohort["d7_eligible"] is False
    assert cohort["d7_rate"] is None

    assert metrics["weekly"]["active_7d"] == 2
    assert metrics["weekly"]["multi_day_7d"] == 1
    assert metrics["weekly"]["volume_rate"] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_flow_reconciliation_and_event_versions(db_session) -> None:
    db = db_session
    now = datetime.now(UTC)
    user = await _user(db, "13800000201", created_at=now)
    await db.commit()

    # 三个客户端意图：两个服务端有事实（其中一个是重复上报），一个丢失。
    for idx, flow_id in enumerate(("flow-a", "flow-a", "flow-b", "flow-c")):
        db.add(
            BehaviorEvent(
                user_id=user.id,
                event_type="flow_result",
                event_payload={"path": "listening", "v": 2},
                flow_id=flow_id,
                schema_version=2,
                event_id=f"evt-{flow_id}-{idx}",
                server_ts=now,
            )
        )
    # 旧客户端事件（v1，没有 event_id）
    db.add(
        BehaviorEvent(
            user_id=user.id,
            event_type="click",
            event_payload={"source": "legacy"},
            schema_version=1,
            server_ts=now,
        )
    )
    await _event(db, user, now.date(), flow_id="flow-a", source="listening")
    await _event(db, user, now.date(), flow_id="flow-b", source="listening")
    # 服务端有事实、客户端没有意图（埋点漏发）
    await _event(db, user, now.date(), flow_id="flow-d", source="listening")
    await db.commit()

    metrics = await learning_metrics(db, days=7)
    flow = next(f for f in metrics["event_quality"]["flows"] if f["path"] == "listening")
    assert flow["client_results"] == 4
    assert flow["client_distinct_flows"] == 3
    assert flow["server_facts"] == 3  # flow-a / flow-b / flow-d
    assert flow["matched"] == 2
    assert flow["client_only"] == 1
    assert flow["server_only"] == 1
    assert flow["duplicate_intents"] == 1
    assert flow["loss_rate"] == pytest.approx(1 / 3, abs=1e-4)

    versions = {e["event_type"]: e for e in metrics["event_quality"]["by_type"]}
    assert versions["click"]["versions"] == {"1": 1}
    assert versions["click"]["missing_event_id_rate"] == 1.0
    assert versions["flow_result"]["versions"] == {"2": 4}
    assert versions["flow_result"]["missing_event_id_rate"] == 0.0


@pytest.mark.asyncio
async def test_performance_samples_and_pipeline_backlog(db_session) -> None:
    db = db_session
    now = datetime.now(UTC)
    user = await _user(db, "13800000301", created_at=now)
    video = Video(
        id="00000000-0000-4000-8000-0000000000bb",
        title="Pipeline Video",
        source_url="https://example.com/v.mp4",
        video_source=VideoSource.imported,
        status=VideoStatus.processing,
    )
    db.add(video)
    await db.commit()

    for i, value in enumerate([1200, 1800, 2400, 3600]):
        db.add(
            BehaviorEvent(
                user_id=user.id,
                event_type="web_vital",
                event_payload={"metric": "lcp", "value": value, "v": 2, "path": "/"},
                schema_version=2,
                event_id=f"vital-{i}",
                server_ts=now,
            )
        )
    db.add(
        BehaviorEvent(
            user_id=user.id,
            event_type="first_play",
            event_payload={"ms": 900, "v": 2},
            schema_version=2,
            event_id="first-play-1",
            server_ts=now,
        )
    )
    db.add(
        PipelineDispatch(
            video_id="00000000-0000-4000-8000-0000000000bb",
            task_name="app.tasks.video_processing.finalize_video",
            args=[],
            status=DISPATCH_STATUS_PENDING,
            created_at=now - timedelta(seconds=125),
        )
    )
    # 派发记录指向不存在的视频会触发外键：SQLite 默认关闭 FK，这里只测聚合。
    await db.commit()

    metrics = await learning_metrics(db, days=7)
    performance = metrics["performance"]
    assert performance["web_vitals"]["lcp"]["samples"] == 4
    assert performance["web_vitals"]["lcp"]["p75"] == 2400
    # 没有 INP/CLS 样本 -> None，而不是 0
    assert performance["web_vitals"]["inp"]["p75"] is None
    assert performance["web_vitals"]["inp"]["samples"] == 0
    assert performance["first_play"]["p75_ms"] == 900
    assert performance["first_play"]["samples"] == 1
    assert performance["pipeline_backlog"]["pending_dispatches"] == 1
    assert performance["pipeline_backlog"]["oldest_pending_age_s"] >= 120


@pytest.mark.asyncio
async def test_admin_metrics_endpoint_requires_admin_and_returns_definitions(
    client, admin_headers, auth_headers
) -> None:
    forbidden = await client.get("/api/v1/admin/metrics/learning", headers=auth_headers)
    assert forbidden.status_code == 403

    resp = await client.get("/api/v1/admin/metrics/learning?days=7", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["days"] == 7
    # 口径随响应返回：看数字的人必须先看到分母定义
    assert body["definitions"]["version"] == "1"
    assert "activation" in body["definitions"]
    assert {"activation", "cohorts", "weekly", "event_quality", "performance"} <= set(body)
    assert set(body["performance"]["web_vitals"]) == {"lcp", "inp", "cls"}


@pytest.mark.asyncio
async def test_behavior_ingest_accepts_flow_id_and_rejects_newer_schema(client) -> None:
    ok = await client.post(
        "/api/v1/behavior/events",
        json={
            "event_type": "flow_result",
            "event_payload": {"path": "listening", "v": 2},
            "flow_id": "11111111-1111-4111-8111-111111111111",
            "schema_version": 2,
            "event_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        },
    )
    assert ok.status_code == 200

    # 客户端比服务端新：拒绝而不是猜测字段含义
    newer = await client.post(
        "/api/v1/behavior/events",
        json={"event_type": "flow_result", "schema_version": 99},
    )
    assert newer.status_code == 422


@pytest.mark.asyncio
async def test_behavior_ingest_accepts_v3_gloss_events(client) -> None:
    """A14：词卡会话事件随契约 v3 上报，且不进「有效学习日」的分母。

    `gloss_open` / `replay` 是交互意图，不是学习事实：它们可以入库、可以按
    flow_id 配对，但一旦被塞进 `MEANINGFUL_EVENT_TYPES`，一次查词就会改变
    激活/留存的分母，历史可比性随之作废。
    """
    for event_type, event_id, payload in (
        ("gloss_open", "33333333-3333-4333-8333-333333333331", {"word": "welcome", "sentence_index": 0}),
        ("replay", "33333333-3333-4333-8333-333333333332", {"sentence_index": 0, "from_gloss": True}),
    ):
        response = await client.post(
            "/api/v1/behavior/events",
            json={
                "event_type": event_type,
                "event_payload": payload,
                "flow_id": "22222222-2222-4222-8222-222222222222",
                "schema_version": 3,
                "event_id": event_id,
            },
        )
        assert response.status_code == 200, response.text

    assert "gloss_open" not in MEANINGFUL_EVENT_TYPES
    assert "replay" not in MEANINGFUL_EVENT_TYPES

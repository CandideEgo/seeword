"""首页编辑内容：草稿 / 不可变版本 / 布局 / 公共读取 / 生成状态机的行为测试。

对应 ``backend/app/schemas/home_content.py`` 与任务文档 §10：

- 草稿/生成结果对普通用户不可见；非管理员不能读写管理接口。
- 草稿保存、生成失败、重新生成都不改变当前首页。
- 发布校验：跨视频字幕、片段顺序、来源变化、视频不可公共展示。
- 布局：乐观锁、字段级 issues、原子发布、恢复上一版、失效拒绝。
- 生成状态机：去重占位、冲突不覆盖、超时恢复、入队失败可见可重试。

AI 在自动化里被 stub（不消耗额度）；生成任务的 Celery 入队被替换成记录器。
"""

from __future__ import annotations

import sys
import types
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.errors import ErrorCode
from app.models.home_content import HomeContentDraft, HomePageConfig
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoStatus
from app.services import home_content_service
from app.services.home_content_service import collect_issues, compute_source_fingerprint

ADMIN = "/api/v1/admin/home-content"
PUBLIC = "/api/v1/browse/home-editorial"

SENTENCES = [
    ("If you look closely, you can spot the difference.", "如果你仔细看，就能发现差别。"),
    ("The color of the sky changes at dusk.", "天空的颜色在黄昏时变化。"),
    ("Most people miss it on the first look.", "大多数人第一次看时会错过。"),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


async def make_video(db, *, title="A closer look", published=True) -> tuple[Video, list[Subtitle]]:
    video = Video(
        title=title,
        source_url=f"https://example.com/{title}",
        video_source="local",
        status=VideoStatus.ready,
        is_official=True,
        is_published=published,
        duration=140.0,
        thumbnail_url="https://example.com/thumb.jpg",
        storage_mode="local",
    )
    db.add(video)
    await db.flush()
    subtitles = [
        Subtitle(
            video_id=video.id,
            sentence_index=index,
            start_time=index * 5.0,
            end_time=index * 5.0 + 4.0,
            text_en=text_en,
            text_zh=text_zh,
        )
        for index, (text_en, text_zh) in enumerate(SENTENCES)
    ]
    db.add_all(subtitles)
    await db.commit()
    return video, subtitles


def draft_payload(
    subtitles: list[Subtitle],
    *,
    headline: str = "换个角度，先看细节",
    dek: str = "用一分钟学会从细节里读懂画面，也顺手记住 spot the difference。",
    clip: dict | None = None,
    expressions: list[dict] | None = None,
) -> dict:
    return {
        "headline": headline,
        "dek": dek,
        "topic_label": "观察",
        "evidence_subtitle_ids": [subtitles[0].id],
        "clip": clip
        if clip is not None
        else {"start_subtitle_id": subtitles[0].id, "end_subtitle_id": subtitles[1].id},
        "expressions": expressions
        if expressions is not None
        else [
            {
                "id": "spot-difference",
                "subtitle_id": subtitles[0].id,
                "phrase": "spot the difference",
                "word": "spot",
                "gloss_zh": "v. 发现；辨认出",
                "note_zh": "口语里常用来指「找出不同」。",
            }
        ],
        "interaction": {
            "id": "first-look",
            "question": "如果是你，会先看哪里？",
            "options": [
                {"id": "detail", "label": "脸和手的细节", "feedback": "你会先注意到人的小动作。"},
                {"id": "color", "label": "颜色和光线", "feedback": "你会先被整体氛围抓住。"},
            ],
        },
        "scenarios": [
            {
                "id": "rain-check",
                "situation_zh": "约朋友·临时有事",
                "prompt_zh": "朋友约你今晚吃饭，试着回一句。",
                "reply_en": "Can I take a rain check?",
                "reply_zh": "这次先不了，下次再约好吗？",
                "subtitle_id": subtitles[1].id,
            }
        ],
    }


async def save_draft(client, headers, video: Video, payload: dict, expected_revision: int = 0):
    return await client.put(
        f"{ADMIN}/videos/{video.id}/draft",
        headers=headers,
        json={"payload": payload, "expected_revision": expected_revision},
    )


async def publish(client, headers, video: Video, expected_revision: int, place: str | None = None):
    return await client.post(
        f"{ADMIN}/videos/{video.id}/publish",
        headers=headers,
        json={"expected_revision": expected_revision, "place": place},
    )


async def get_state(client, headers, video: Video) -> dict:
    response = await client.get(f"{ADMIN}/videos/{video.id}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def public_page(client) -> dict | None:
    response = await client.get(PUBLIC)
    assert response.status_code == 200, response.text
    return response.json()["editorial"]


def admin_endpoint_calls(video_id: str, subtitles: list[Subtitle]) -> list[tuple[str, str, dict | None]]:
    """admin 端点全集：``(method, path, body)``，每条都要有一次越权断言。

    写路径（保存草稿 / 发布 / 恢复草稿 / 布局发布与回滚）**一个都不能漏**：
    越权写入的后果比越权读取更重（能把首页内容替换掉）。
    """
    return [
        # --- 读 ---
        ("get", f"{ADMIN}/videos/{video_id}", None),
        ("get", f"{ADMIN}/videos/{video_id}/generation", None),
        ("get", f"{ADMIN}/videos/{video_id}/preview", None),
        ("get", f"{ADMIN}/layout", None),
        ("get", f"{ADMIN}/layout/preview", None),
        # --- 写 ---
        ("post", f"{ADMIN}/videos/{video_id}/generate", {"expected_revision": 0}),
        ("put", f"{ADMIN}/videos/{video_id}/draft", {"payload": draft_payload(subtitles), "expected_revision": 0}),
        ("post", f"{ADMIN}/videos/{video_id}/publish", {"expected_revision": 0}),
        ("post", f"{ADMIN}/videos/{video_id}/restore-draft", {"revision_id": "rev-1", "expected_revision": 0}),
        ("put", f"{ADMIN}/layout/draft", {"layout": {}, "expected_revision": 0}),
        ("post", f"{ADMIN}/layout/publish", {"expected_revision": 0}),
        ("post", f"{ADMIN}/layout/rollback", {"expected_revision": 0}),
    ]


# ---------------------------------------------------------------------------
# 指纹与校验（纯函数）
# ---------------------------------------------------------------------------


def test_fingerprint_covers_content_and_ignores_float_tails():
    subtitle = SimpleNamespace(
        id="sub-1",
        sentence_index=0,
        start_time=0.0,
        end_time=1.25,
        text_en="Hello there.",
        text_zh="你好。",
    )
    fingerprint = compute_source_fingerprint([subtitle])
    assert len(fingerprint) == 64
    assert fingerprint == compute_source_fingerprint([subtitle])
    changed_text = SimpleNamespace(**{**subtitle.__dict__, "text_en": "Hello there!"})
    assert compute_source_fingerprint([changed_text]) != fingerprint
    changed_index = SimpleNamespace(**{**subtitle.__dict__, "sentence_index": 1})
    assert compute_source_fingerprint([changed_index]) != fingerprint
    # 3 位小数：0.0004 的尾差不应让版本失效。
    tail = SimpleNamespace(**{**subtitle.__dict__, "start_time": 0.0004})
    assert compute_source_fingerprint([tail]) == fingerprint


def test_collect_issues_reports_cross_video_and_phrase_problems():
    subtitles = [
        SimpleNamespace(
            id=f"sub-{index}",
            sentence_index=index,
            start_time=float(index),
            end_time=float(index) + 0.5,
            text_en=text,
            text_zh=None,
            words=None,
        )
        for index, text in enumerate(("You can spot it.", "Dusk falls.", "Look again."))
    ]
    payload = {
        "headline": "标题",
        "dek": "导语",
        "topic_label": None,
        "evidence_subtitle_ids": ["missing"],
        "clip": {"start_subtitle_id": "sub-2", "end_subtitle_id": "sub-0"},
        "expressions": [
            {
                "id": "expr-one",
                "subtitle_id": "sub-0",
                "phrase": "spot it",
                "word": "spot",
                "gloss_zh": None,
                "note_zh": None,
            },
            {
                "id": "expr-two",
                "subtitle_id": "sub-0",
                "phrase": "invented phrase",
                "word": None,
                "gloss_zh": None,
                "note_zh": None,
            },
        ],
        "interaction": None,
        "scenarios": [],
    }
    issues = collect_issues(payload, subtitles, strict=True)
    fields = {issue.field for issue in issues}
    assert "evidence_subtitle_ids[0]" in fields
    assert "clip" in fields
    assert "expressions[1].phrase" in fields


# ---------------------------------------------------------------------------
# 可见性与鉴权
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_public_endpoint_needs_no_auth_and_defaults_to_null(client):
    response = await client.get(PUBLIC)
    assert response.status_code == 200
    assert response.json() == {"editorial": None}


@pytest.mark.asyncio
async def test_non_admin_cannot_read_or_write_admin_home_content(client, auth_headers, db_session):
    video, subtitles = await make_video(db_session)
    for method, path, body in admin_endpoint_calls(video.id, subtitles):
        kwargs = {"headers": auth_headers}
        if body is not None:
            kwargs["json"] = body
        response = await getattr(client, method)(path, **kwargs)
        assert response.status_code == 403, (path, response.text)
        assert response.json()["code"] == "HTTP_403"


@pytest.mark.asyncio
async def test_every_admin_endpoint_has_a_forbidden_assertion(client, auth_headers, db_session):
    """admin 端点全集必须逐个有越权断言：新增端点忘了加，这里就红。

    只靠人肉数 ``calls`` 列表会漏（这正是之前漏掉 5 个写路径的原因），
    所以把「断言覆盖的路径」与「应用真实注册的 admin 路由」直接对表。
    """
    from app.main import create_app

    video, subtitles = await make_video(db_session)
    asserted = {
        path.replace(video.id, "{video_id}") for _method, path, _body in admin_endpoint_calls(video.id, subtitles)
    }
    # 用应用自己的 OpenAPI 视图取「真实注册的 admin 路由」，
    # 不去数 router.routes（FastAPI 新版本那里是嵌套结构，取不到 path）。
    registered = {path for path in create_app().openapi()["paths"] if path.startswith(f"{ADMIN}/")}

    assert registered == asserted
    assert len(asserted) == 12


# ---------------------------------------------------------------------------
# 草稿
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_draft_roundtrip_and_optimistic_lock(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    state = await get_state(client, admin_headers, video)
    assert state["draft"] is None
    assert state["draft_revision"] == 0
    assert state["generation"] is None
    assert state["publicly_visible"] is True
    assert len(state["source_fingerprint"]) == 64

    response = await save_draft(client, admin_headers, video, draft_payload(subtitles))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["draft"]["headline"] == "换个角度，先看细节"
    assert body["draft_revision"] == 1

    conflict = await save_draft(client, admin_headers, video, draft_payload(subtitles), expected_revision=0)
    assert conflict.status_code == 409
    assert conflict.json()["code"] == ErrorCode.HOME_CONTENT_REVISION_CONFLICT

    state = await get_state(client, admin_headers, video)
    assert state["draft"]["expressions"][0]["phrase"] == "spot the difference"
    assert state["revisions"] == []


@pytest.mark.asyncio
async def test_save_draft_rejects_foreign_and_invented_references(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    _, other_subtitles = await make_video(db_session, title="Other clip")

    foreign = draft_payload(subtitles)
    foreign["evidence_subtitle_ids"] = [other_subtitles[0].id]
    response = await save_draft(client, admin_headers, video, foreign)
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == ErrorCode.HOME_CONTENT_INVALID
    assert any(item["code"] == "SUBTITLE_NOT_IN_VIDEO" for item in body["detail"])

    invented = draft_payload(
        subtitles,
        expressions=[
            {
                "id": "not-in-caption",
                "subtitle_id": subtitles[0].id,
                "phrase": "ghost words",
                "word": None,
                "gloss_zh": None,
                "note_zh": None,
            }
        ],
    )
    response = await save_draft(client, admin_headers, video, invented)
    assert response.status_code == 422
    assert any(item["code"] == "PHRASE_NOT_IN_SUBTITLE" for item in response.json()["detail"])

    reversed_clip = draft_payload(
        subtitles,
        clip={"start_subtitle_id": subtitles[2].id, "end_subtitle_id": subtitles[0].id},
    )
    response = await save_draft(client, admin_headers, video, reversed_clip)
    assert response.status_code == 422
    assert any(item["code"] == "CLIP_ORDER_INVALID" for item in response.json()["detail"])


# ---------------------------------------------------------------------------
# 发布
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_publish_incomplete_draft_is_rejected_with_field_level_detail(client, admin_headers, db_session):
    video, _ = await make_video(db_session)
    empty = {
        "headline": "",
        "dek": "",
        "topic_label": None,
        "evidence_subtitle_ids": [],
        "clip": None,
        "expressions": [],
        "interaction": None,
        "scenarios": [],
    }
    assert (await save_draft(client, admin_headers, video, empty)).status_code == 200
    response = await publish(client, admin_headers, video, expected_revision=1)
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == ErrorCode.HOME_CONTENT_INVALID
    fields = {item["field"] for item in body["detail"]}
    assert {"headline", "dek", "clip", "expressions"} <= fields


@pytest.mark.asyncio
async def test_publish_creates_immutable_revision_and_public_page(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    response = await save_draft(client, admin_headers, video, draft_payload(subtitles))
    assert response.status_code == 200

    published = await publish(client, admin_headers, video, expected_revision=1, place="lead")
    assert published.status_code == 200, published.text
    first = published.json()
    assert first["version"] == 1
    assert isinstance(first["layout_revision"], int)

    editorial = await public_page(client)
    assert editorial is not None
    lead = editorial["lead"]
    assert lead["content"]["content_revision_id"] == first["revision_id"]
    assert lead["content"]["video_id"] == video.id
    assert lead["video"]["id"] == video.id
    assert lead["content"]["headline"] == "换个角度，先看细节"
    assert lead["content"]["clip"]["duration"] == pytest.approx(9.0)
    assert lead["content"]["expressions"][0]["phrase"] == "spot the difference"
    assert lead["content"]["interaction"]["options"][0]["feedback"]
    assert lead["content"]["scenarios"][0]["reply_en"] == "Can I take a rain check?"
    assert lead["content"]["scenarios"][0]["sentence"]["text_en"] == SENTENCES[1][0]
    texts = [sentence["text_en"] for sentence in lead["content"]["sentences"]]
    assert SENTENCES[0][0] in texts and SENTENCES[1][0] in texts
    assert editorial["secondary"] == []

    state = await get_state(client, admin_headers, video)
    assert [revision["version"] for revision in state["revisions"]] == [1]
    assert state["revisions"][0]["positions"] == ["lead"]
    assert state["positions"] == ["lead"]
    assert state["revisions"][0]["headline"] == "换个角度，先看细节"
    assert state["source_changed"] is False

    # 编辑草稿不影响线上；再次发布（不带 place）也不改变布局引用。
    updated = draft_payload(subtitles, headline="新的标题")
    assert (await save_draft(client, admin_headers, video, updated, expected_revision=1)).status_code == 200
    assert (await public_page(client))["lead"]["content"]["headline"] == "换个角度，先看细节"
    second = await publish(client, admin_headers, video, expected_revision=2)
    assert second.status_code == 200
    assert second.json()["version"] == 2
    assert (await public_page(client))["lead"]["content"]["headline"] == "换个角度，先看细节"

    # 「发布并替换主推」才让线上换成新版本。
    third = await publish(client, admin_headers, video, expected_revision=2, place="lead")
    assert third.status_code == 200
    assert third.json()["version"] == 3
    assert (await public_page(client))["lead"]["content"]["headline"] == "新的标题"


@pytest.mark.asyncio
async def test_publish_rejects_changed_source_and_restored_source_state(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    subtitles[0].text_en = "If you look closely, you can spot every difference."
    await db_session.commit()

    response = await publish(client, admin_headers, video, expected_revision=1)
    assert response.status_code == 422
    assert response.json()["code"] == ErrorCode.HOME_CONTENT_SOURCE_CHANGED
    state = await get_state(client, admin_headers, video)
    assert state["source_changed"] is True
    assert state["revisions"] == []


@pytest.mark.asyncio
async def test_publish_rejects_non_public_video(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session, published=False)
    state = await get_state(client, admin_headers, video)
    assert state["publicly_visible"] is False
    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    response = await publish(client, admin_headers, video, expected_revision=1)
    assert response.status_code == 422
    assert response.json()["code"] == ErrorCode.HOME_CONTENT_VIDEO_NOT_PUBLIC


@pytest.mark.asyncio
async def test_restore_draft_copies_history_without_touching_public_page(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    published = await publish(client, admin_headers, video, expected_revision=1, place="lead")
    revision_id = published.json()["revision_id"]

    changed = draft_payload(subtitles, headline="改过的标题")
    assert (await save_draft(client, admin_headers, video, changed, expected_revision=1)).status_code == 200
    assert (await public_page(client))["lead"]["content"]["headline"] == "换个角度，先看细节"

    response = await client.post(
        f"{ADMIN}/videos/{video.id}/restore-draft",
        headers=admin_headers,
        json={"revision_id": revision_id, "expected_revision": 2},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["draft"]["headline"] == "换个角度，先看细节"
    assert body["draft_revision"] == 3
    assert (await public_page(client))["lead"]["content"]["headline"] == "换个角度，先看细节"

    stale = await client.post(
        f"{ADMIN}/videos/{video.id}/restore-draft",
        headers=admin_headers,
        json={"revision_id": revision_id, "expected_revision": 2},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == ErrorCode.HOME_CONTENT_REVISION_CONFLICT


# ---------------------------------------------------------------------------
# 预览
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_video_preview_returns_page_and_publish_issues(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    response = await client.get(f"{ADMIN}/videos/{video.id}/preview", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["page"] is None
    assert response.json()["issues"][0]["code"] == "DRAFT_EMPTY"

    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    response = await client.get(f"{ADMIN}/videos/{video.id}/preview", headers=admin_headers)
    body = response.json()
    assert body["issues"] == []
    assert body["page"]["lead"]["content"]["headline"] == "换个角度，先看细节"

    incomplete = draft_payload(subtitles, headline="")
    assert (await save_draft(client, admin_headers, video, incomplete, expected_revision=1)).status_code == 200
    response = await client.get(f"{ADMIN}/videos/{video.id}/preview", headers=admin_headers)
    body = response.json()
    assert any(issue["field"] == "headline" for issue in body["issues"])
    assert body["page"] is not None  # 预览尽力构造，不被 issues 挡住


# ---------------------------------------------------------------------------
# 布局
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_layout_draft_publish_preview_and_rollback(client, admin_headers, db_session):
    video_a, subtitles_a = await make_video(db_session, title="Video A")
    video_b, subtitles_b = await make_video(db_session, title="Video B")
    for video, subtitles in ((video_a, subtitles_a), (video_b, subtitles_b)):
        assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
        assert (await publish(client, admin_headers, video, expected_revision=1)).status_code == 200

    state = await get_state(client, admin_headers, video_a)
    revision_a = state["revisions"][0]["id"]
    revision_b = (await get_state(client, admin_headers, video_b))["revisions"][0]["id"]

    layout = (await client.get(f"{ADMIN}/layout", headers=admin_headers)).json()
    assert layout["revision"] == 0
    assert layout["draft_layout"] == {"lead": None, "secondary": [], "expression": None, "scenarios": []}
    assert layout["published_active"] is False
    assert {candidate["content_revision_id"] for candidate in layout["candidates"]} == {revision_a, revision_b}

    first_layout = {
        "lead": {"content_revision_id": revision_a},
        "secondary": [{"content_revision_id": revision_b}],
        "expression": {"content_revision_id": revision_a, "expression_id": "spot-difference"},
        "scenarios": [{"content_revision_id": revision_b, "scenario_id": "rain-check"}],
    }
    saved = await client.put(
        f"{ADMIN}/layout/draft",
        headers=admin_headers,
        json={"layout": first_layout, "expected_revision": 0},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["revision"] == 1
    assert saved.json()["issues"] == []

    preview = await client.get(f"{ADMIN}/layout/preview", headers=admin_headers)
    assert preview.status_code == 200
    assert preview.json()["page"]["lead"]["content"]["video_id"] == video_a.id
    assert preview.json()["page"]["secondary"][0]["content"]["video_id"] == video_b.id
    assert preview.json()["page"]["expression"]["expression_id"] == "spot-difference"
    assert preview.json()["page"]["scenarios"][0]["scenario_id"] == "rain-check"

    published = await client.post(f"{ADMIN}/layout/publish", headers=admin_headers, json={"expected_revision": 1})
    assert published.status_code == 200, published.text
    assert published.json()["layout_revision"] == 2
    editorial = await public_page(client)
    assert editorial["lead"]["content"]["video_id"] == video_a.id
    assert editorial["secondary"][0]["content"]["video_id"] == video_b.id

    # 第二次整版发布：主次互换；再回滚应回到第一版布局（而不是最早的空布局）。
    second_layout = {
        "lead": {"content_revision_id": revision_b},
        "secondary": [{"content_revision_id": revision_a}],
        "expression": None,
        "scenarios": [],
    }
    saved = await client.put(
        f"{ADMIN}/layout/draft",
        headers=admin_headers,
        json={"layout": second_layout, "expected_revision": 2},
    )
    assert saved.status_code == 200, saved.text
    published = await client.post(f"{ADMIN}/layout/publish", headers=admin_headers, json={"expected_revision": 3})
    assert published.status_code == 200, published.text
    assert (await public_page(client))["lead"]["content"]["video_id"] == video_b.id

    rolled_back = await client.post(f"{ADMIN}/layout/rollback", headers=admin_headers, json={"expected_revision": 4})
    assert rolled_back.status_code == 200, rolled_back.text
    editorial = await public_page(client)
    assert editorial["lead"]["content"]["video_id"] == video_a.id
    assert editorial["secondary"][0]["content"]["video_id"] == video_b.id
    assert editorial["expression"]["expression_id"] == "spot-difference"


@pytest.mark.asyncio
async def test_layout_optimistic_lock_and_invalid_reference(client, admin_headers, db_session):
    video, subtitles = await make_video(db_session)
    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    assert (await publish(client, admin_headers, video, expected_revision=1, place="lead")).status_code == 200

    bad_layout = {
        "lead": {"content_revision_id": "does-not-exist"},
        "secondary": [],
        "expression": None,
        "scenarios": [],
    }
    current = (await client.get(f"{ADMIN}/layout", headers=admin_headers)).json()
    assert current["revision"] == 1  # 「发布并替换主推」也 +1
    assert current["published_active"] is True
    saved = await client.put(
        f"{ADMIN}/layout/draft",
        headers=admin_headers,
        json={"layout": bad_layout, "expected_revision": current["revision"]},
    )
    assert saved.status_code == 200
    assert any(issue["code"] == "REVISION_NOT_FOUND" for issue in saved.json()["issues"])
    assert saved.json()["published_active"] is True  # 草稿坏了不影响线上

    conflict = await client.put(
        f"{ADMIN}/layout/draft",
        headers=admin_headers,
        json={"layout": bad_layout, "expected_revision": current["revision"]},
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == ErrorCode.HOME_CONTENT_REVISION_CONFLICT

    rejected = await client.post(
        f"{ADMIN}/layout/publish", headers=admin_headers, json={"expected_revision": saved.json()["revision"]}
    )
    assert rejected.status_code == 422
    assert rejected.json()["code"] == ErrorCode.HOME_CONTENT_LAYOUT_INVALID
    assert rejected.json()["detail"][0]["field"] == "lead"


@pytest.mark.asyncio
async def test_rollback_refuses_layout_with_offline_video(client, admin_headers, db_session):
    video_a, subtitles_a = await make_video(db_session, title="Video A")
    video_b, subtitles_b = await make_video(db_session, title="Video B")
    for video, subtitles in ((video_a, subtitles_a), (video_b, subtitles_b)):
        assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
        assert (await publish(client, admin_headers, video, expected_revision=1, place="lead")).status_code == 200
    assert (await public_page(client))["lead"]["content"]["video_id"] == video_b.id

    video_a.is_published = False
    await db_session.commit()

    response = await client.post(f"{ADMIN}/layout/rollback", headers=admin_headers, json={"expected_revision": 2})
    assert response.status_code == 409
    assert response.json()["code"] == ErrorCode.HOME_CONTENT_ROLLBACK_INVALID
    assert any(item["code"] == "VIDEO_NOT_PUBLIC" for item in response.json()["detail"])
    assert (await public_page(client))["lead"]["content"]["video_id"] == video_b.id


@pytest.mark.asyncio
async def test_rollback_without_previous_clears_to_old_fallback(client, admin_headers, db_session):
    """首次发布后 previous 为 null：回滚应原子撤下新编排、回到旧兜底，而不是 409。"""
    video, subtitles = await make_video(db_session)
    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    assert (await publish(client, admin_headers, video, expected_revision=1, place="lead")).status_code == 200
    assert (await public_page(client))["lead"]["content"]["video_id"] == video.id

    layout = (await client.get(f"{ADMIN}/layout", headers=admin_headers)).json()
    assert layout["published_layout"]["lead"] is not None
    assert layout["previous_published_layout"] is None

    rolled_back = await client.post(
        f"{ADMIN}/layout/rollback", headers=admin_headers, json={"expected_revision": layout["revision"]}
    )
    assert rolled_back.status_code == 200, rolled_back.text
    body = rolled_back.json()
    assert body["cleared"] is True
    assert body["layout_revision"] == layout["revision"] + 1
    assert (await public_page(client)) is None  # 公共接口回 null → 首页走旧兜底

    state = (await client.get(f"{ADMIN}/layout", headers=admin_headers)).json()
    assert state["published_layout"] is None
    assert state["published_active"] is False
    assert state["published_revision"] == body["layout_revision"]
    # 撤下的布局留在 previous，便于「再前进」；draft_layout 不被清空。
    assert state["previous_published_layout"]["lead"] is not None
    assert state["draft_layout"]["lead"] is not None

    republished = await client.post(
        f"{ADMIN}/layout/publish", headers=admin_headers, json={"expected_revision": body["layout_revision"]}
    )
    assert republished.status_code == 200, republished.text
    assert "cleared" not in republished.json()  # 发布接口不返回 cleared
    assert (await public_page(client))["lead"]["content"]["video_id"] == video.id


# ---------------------------------------------------------------------------
# 生成状态机
# ---------------------------------------------------------------------------


@pytest.fixture
def dispatched(monkeypatch):
    """替换 Celery 入队为记录器（AI/队列在测试里不真的动）。"""
    calls: list[str] = []

    async def _record(db, claim):
        del db
        calls.append(claim.generation_id)

    monkeypatch.setattr(home_content_service, "enqueue_generation", _record)
    return calls


@pytest.mark.asyncio
async def test_generation_claim_dedupes_and_requires_overwrite(client, admin_headers, db_session, dispatched):
    video, subtitles = await make_video(db_session)
    response = await client.post(
        f"{ADMIN}/videos/{video.id}/generate", headers=admin_headers, json={"expected_revision": 0}
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["reused"] is False
    assert body["generation"]["status"] == "queued"
    generation_id = body["generation"]["generation_id"]
    assert dispatched == [generation_id]

    again = await client.post(
        f"{ADMIN}/videos/{video.id}/generate", headers=admin_headers, json={"expected_revision": 0}
    )
    assert again.status_code == 200
    assert again.json()["reused"] is True
    assert again.json()["generation"]["generation_id"] == generation_id
    assert dispatched == [generation_id]

    state = await get_state(client, admin_headers, video)
    assert state["generation"]["status"] == "queued"

    # 已有草稿时重新生成必须先确认覆盖（409），旧草稿保留。
    assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
    assert await home_content_service.fail_generation(db_session, generation_id, ErrorCode.CONFLICT, "取消")
    overwrite_needed = await client.post(
        f"{ADMIN}/videos/{video.id}/generate", headers=admin_headers, json={"expected_revision": 1}
    )
    assert overwrite_needed.status_code == 409
    assert overwrite_needed.json()["code"] == ErrorCode.HOME_CONTENT_OVERWRITE_CONFIRM


@pytest.mark.asyncio
async def test_generation_success_and_conflict_does_not_override_admin_edit(
    client, admin_headers, db_session, dispatched
):
    video, subtitles = await make_video(db_session)
    started = await client.post(
        f"{ADMIN}/videos/{video.id}/generate", headers=admin_headers, json={"expected_revision": 0}
    )
    assert started.status_code == 202
    generation_id = started.json()["generation"]["generation_id"]

    context = await home_content_service.load_generation_context(db_session, generation_id)
    assert context is not None
    assert context.video_title == video.title
    assert [subtitle.id for subtitle in context.subtitles] == [subtitle.id for subtitle in subtitles]
    state = await get_state(client, admin_headers, video)
    assert state["generation"]["status"] == "running"

    generated = draft_payload(subtitles, headline="AI 生成的标题")
    assert await home_content_service.complete_generation(
        db_session,
        generation_id,
        generated,
        model="test-model",
        prompt_version="v1",
        usage={"prompt_tokens": 120, "completion_tokens": 240},
        calls=1,
    )
    state = await get_state(client, admin_headers, video)
    assert state["draft"]["headline"] == "AI 生成的标题"
    assert state["draft_revision"] == 1
    assert state["generation"]["status"] == "succeeded"
    assert state["generation"]["generation_id"] == generation_id
    assert state["generation"]["model"] == "test-model"
    assert state["generation"]["prompt_version"] == "v1"
    assert state["generation"]["usage"] == {"prompt_tokens": 120, "completion_tokens": 240}
    assert (await public_page(client)) is None  # 生成成功≠发布

    # 新任务 + 管理员中途编辑 → 旧结果晚到也不能覆盖。
    claimed = await home_content_service.claim_generation(db_session, video.id, None, overwrite=True)
    admin_edit = draft_payload(subtitles, headline="管理员手写标题")
    assert (await save_draft(client, admin_headers, video, admin_edit, expected_revision=1)).status_code == 200
    # HTTP 请求用的是另一个 session：显式刷新本 session 里的草稿快照，模拟
    # worker 重新读库（不能 expire_all——字幕 ORM 行会整体过期，属性访问触发 IO）。
    draft_row = (
        await db_session.execute(select(HomeContentDraft).where(HomeContentDraft.video_id == video.id))
    ).scalar_one()
    await db_session.refresh(draft_row)
    assert not await home_content_service.complete_generation(
        db_session, claimed.generation_id, draft_payload(subtitles, headline="迟到的 AI 标题")
    )
    state = await get_state(client, admin_headers, video)
    assert state["draft"]["headline"] == "管理员手写标题"
    assert state["generation"]["status"] == "failed"
    assert state["generation"]["error_code"] == ErrorCode.HOME_CONTENT_CONFLICT


@pytest.mark.asyncio
async def test_generation_source_change_and_invalid_output_are_visible(client, admin_headers, db_session, dispatched):
    video, subtitles = await make_video(db_session)
    claimed = await home_content_service.claim_generation(db_session, video.id, None)
    subtitles[0].text_en = "If you look closely, you can spot the difference here."
    await db_session.commit()
    assert not await home_content_service.complete_generation(
        db_session, claimed.generation_id, draft_payload(subtitles)
    )
    state = await get_state(client, admin_headers, video)
    assert state["generation"]["status"] == "failed"
    assert state["generation"]["error_code"] == ErrorCode.HOME_CONTENT_SOURCE_CHANGED

    claimed = await home_content_service.claim_generation(db_session, video.id, None)
    assert not await home_content_service.complete_generation(
        db_session, claimed.generation_id, {"headline": "缺字段的 AI 输出"}
    )
    state = await get_state(client, admin_headers, video)
    assert state["generation"]["status"] == "failed"
    assert state["generation"]["error_code"] == ErrorCode.HOME_CONTENT_AI_INVALID


@pytest.mark.asyncio
async def test_generation_timeout_recovery_and_enqueue_failure(client, admin_headers, db_session, monkeypatch):
    video, _ = await make_video(db_session)
    claimed = await home_content_service.claim_generation(db_session, video.id, None)
    draft = (
        await db_session.execute(select(HomeContentDraft).where(HomeContentDraft.video_id == video.id))
    ).scalar_one()
    draft.generation_started_at = datetime.now(UTC) - timedelta(
        seconds=home_content_service.GENERATION_STALE_SECONDS + 60
    )
    await db_session.commit()

    # GET 状态顺带恢复：不再永久卡在 queued。
    response = await client.get(f"{ADMIN}/videos/{video.id}/generation", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["generation"]["status"] == "failed"
    assert response.json()["generation"]["error_code"] == ErrorCode.HOME_CONTENT_TIMEOUT

    # beat 巡检兜底同样处理卡死任务。
    claimed = await home_content_service.claim_generation(db_session, video.id, None)
    draft = (
        await db_session.execute(select(HomeContentDraft).where(HomeContentDraft.video_id == video.id))
    ).scalar_one()
    draft.generation_started_at = datetime.now(UTC) - timedelta(
        seconds=home_content_service.GENERATION_STALE_SECONDS + 60
    )
    await db_session.commit()
    assert await home_content_service.sweep_stale_generations(db_session) == 1
    state = await get_state(client, admin_headers, video)
    assert state["generation"]["status"] == "failed"
    assert state["generation"]["error_code"] == ErrorCode.HOME_CONTENT_TIMEOUT

    # 入队失败：503 + 草稿置 failed（可重试），不伪装成功。
    fake_module = types.ModuleType("app.tasks.home_content_tasks")

    def _raise(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("broker down")

    fake_module.generate_home_content_draft = SimpleNamespace(apply_async=_raise)
    monkeypatch.setitem(sys.modules, "app.tasks.home_content_tasks", fake_module)
    new_claim = await home_content_service.claim_generation(db_session, video.id, None)
    del claimed
    with pytest.raises(Exception) as raised:
        await home_content_service.enqueue_generation(db_session, new_claim)
    assert getattr(raised.value, "status_code", None) == 503
    assert getattr(raised.value, "code", None) == ErrorCode.HOME_CONTENT_ENQUEUE_FAILED
    state = await get_state(client, admin_headers, video)
    assert state["generation"]["status"] == "failed"
    assert state["generation"]["error_code"] == ErrorCode.HOME_CONTENT_ENQUEUE_FAILED


@pytest.mark.asyncio
async def test_public_page_drops_stale_and_offline_content(client, admin_headers, db_session):
    video_a, subtitles_a = await make_video(db_session, title="Video A")
    video_b, subtitles_b = await make_video(db_session, title="Video B")
    for video, subtitles, place in ((video_a, subtitles_a, "lead"), (video_b, subtitles_b, "secondary")):
        assert (await save_draft(client, admin_headers, video, draft_payload(subtitles))).status_code == 200
        assert (await publish(client, admin_headers, video, expected_revision=1, place=place)).status_code == 200

    editorial = await public_page(client)
    assert editorial["lead"]["content"]["video_id"] == video_a.id
    assert [slot["content"]["video_id"] for slot in editorial["secondary"]] == [video_b.id]

    # 次推视频下线 → 该卡被过滤，主推不受影响。
    video_b.is_published = False
    await db_session.commit()
    editorial = await public_page(client)
    assert editorial["lead"]["content"]["video_id"] == video_a.id
    assert editorial["secondary"] == []

    # 主推字幕变化 → 版本失效；没有可提升的次推 → 整块退回旧兜底（null）。
    subtitles_a[0].text_en = "Completely different sentence now."
    await db_session.commit()
    assert (await public_page(client)) is None

    state = await get_state(client, admin_headers, video_a)
    assert state["revisions"][0]["source_changed"] is True
    # 位置仍保留在布局里（后台需要看到「这个版本被摆在哪」），只是公共卡片被过滤掉。
    assert state["revisions"][0]["positions"] == ["lead"]


@pytest.mark.asyncio
async def test_generation_endpoint_requires_existing_video(client, admin_headers):
    response = await client.get(f"{ADMIN}/videos/not-a-real-video", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["code"] == ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_no_scheduled_layout_leaves_public_fallback_and_empty_config(client, db_session):
    """旧兜底仍然可用：没有编排时公共接口返回 null，读接口不写任何配置行。"""
    assert (await public_page(client)) is None
    rows = (await db_session.execute(select(HomePageConfig))).scalars().all()
    assert rows == []

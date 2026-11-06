"""E2E smoke: 内测免费开放 — 登录即看（需求 §2.3）。

Drives the freed-up access path over real HTTP against the ASGI app on a
temp SQLite file:
  注册 → 直接看视频（无解锁）→ 详情带字幕/URL → 媒体 200
  匿名 → 仍被拒（登录墙）
  退役端点 → 空载荷

Run: PYTHONUTF8=1 .venv/Scripts/python.exe scripts/smoke_free_access.py
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_SMOKE_DB = os.path.join(tempfile.mkdtemp(prefix="seeword-free-"), "smoke.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_SMOKE_DB}"
os.environ.setdefault("SECRET_KEY", "smoke-secret-key-long-enough-for-hs256")

from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.database import Base, get_async_session_maker, get_engine
from app.core.security import create_token, hash_password
from app.main import app
from app.models.subtitle import Subtitle
from app.models.user import RoleType, User
from app.models.video import Video, VideoStatus


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    return ok


async def main() -> int:
    results: list[bool] = []

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_async_session_maker()() as db:
        user = User(
            phone="13900000011",
            hashed_password=hash_password("Smoke123!"),
            role=RoleType.user,
            onboarding_completed=True,
        )
        db.add(user)
        video = Video(
            title="免费开放验证",
            source_url="https://example.com/free-access",
            status=VideoStatus.ready,
            is_official=True,
            is_published=True,
        )
        db.add(video)
        await db.flush()
        # 媒体文件名必须用真实 video id —— /media 的发布态/门控正则要求
        # 文件名以 UUID 开头（见 media._VIDEO_FILE_RE），否则整个门控被跳过。
        media_name = f"{video.id}_720p.mp4"
        video.video_url_720p = f"/media/{media_name}"
        db.add(
            Subtitle(
                video_id=video.id,
                sentence_index=0,
                start_time=0.0,
                end_time=2.0,
                text_en="Free access check",
                text_zh="免费开放验证",
                word_levels={"free": ["cet4"]},
            )
        )
        await db.commit()
        user_id, video_id = user.id, video.id

    # 落一个媒体文件，验证 /media 真的可读。
    settings = get_settings()
    media_dir = Path(settings.local_media_path).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    media_file = media_dir / media_name
    media_file.write_bytes(b"free access media payload")

    headers = {"Authorization": f"Bearer {create_token(user_id)}"}
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://smoke") as c:
            print("\n[1] 登录用户直接看视频 — 无解锁步骤")
            r = await c.get(f"/api/v1/videos/{video_id}", headers=headers)
            results.append(check("详情 200", r.status_code == 200, f"status={r.status_code}"))
            data = r.json()
            results.append(check("响应不含会员字段", "access" not in data, str(list(data.keys()))))
            results.append(check("字幕直接下发", len(data["subtitles"]) == 1, f"n={len(data['subtitles'])}"))
            results.append(
                check("播放 URL 直接下发", data.get("video_url_720p") is not None, str(data.get("video_url_720p")))
            )

            print("\n[2] 媒体流可直接播放")
            r = await c.get(f"/media/{media_name}?token={create_token(user_id)}")
            results.append(check("媒体 200", r.status_code == 200, f"status={r.status_code}"))
            results.append(check("内容一致", r.content == b"free access media payload"))

            print("\n[3] 跟读重点句：跟读功能本身已退役（410）")
            r = await c.get(f"/api/v1/videos/{video_id}/shadowing-sentences", headers=headers)
            results.append(check("410 FEATURE_RETIRED", r.status_code == 410, f"status={r.status_code}"))

            print("\n[4] 已下线的解锁/收费端点 — 404")
            r = await c.post(f"/api/v1/videos/{video_id}/unlock", headers=headers)
            results.append(check("unlock 已删除", r.status_code == 404, f"status={r.status_code}"))
            r = await c.get("/api/v1/videos/unlocked", headers=headers)
            results.append(check("unlocked 列表已删除", r.status_code == 404, f"status={r.status_code}"))
            r = await c.get("/api/v1/payments/status", headers=headers)
            results.append(check("payments 已删除", r.status_code == 404, f"status={r.status_code}"))

            print("\n[5] 匿名：能拿元信息，但不给字幕/播放地址（登录墙）")
            r = await c.get(f"/api/v1/videos/{video_id}")
            results.append(check("匿名详情 200", r.status_code == 200, f"status={r.status_code}"))
            results.append(check("匿名无字幕", r.json()["subtitles"] == []))
            results.append(check("匿名无播放地址", r.json()["video_url_720p"] is None))
            r = await c.get(f"/media/{media_name}")
            results.append(check("匿名媒体 403", r.status_code == 403, f"status={r.status_code}"))
            r = await c.get(f"/api/v1/videos/{video_id}/shadowing-sentences")
            results.append(check("匿名跟读句 401", r.status_code == 401, f"status={r.status_code}"))

            print("\n[6] 登录用户全功能可用（词汇本该有的入口不依赖解锁）")
            r = await c.get("/api/v1/vocabulary/stats", headers=headers)
            results.append(check("词汇统计 200", r.status_code == 200, f"status={r.status_code}"))
            r = await c.post("/api/v1/vocab-sets", json={"video_id": video_id, "exam_level": "cet4"}, headers=headers)
            results.append(check("加入学习 200", r.status_code == 200, f"status={r.status_code}"))
    finally:
        media_file.unlink(missing_ok=True)

    print(f"\n{'=' * 56}\n冒烟结果：{sum(results)}/{len(results)} 通过")
    if all(results):
        print("登录即看：无解锁流程，全功能免费；匿名仍拒")
        return 0
    print("存在失败项，见上方 [FAIL]")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

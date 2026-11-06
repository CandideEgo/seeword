#!/usr/bin/env python3
"""A08 / BE-04 隔离演练：数据导出完整性与注销清理。

在一次性 Postgres（隔离 compose 的 ``pg`` profile，127.0.0.1:15432）与临时媒体目录
上跑真实的服务/任务代码：

1. 两个账号 A/B，各自一套代表性数据与媒体；
2. A 的导出 ZIP 必须包含全部区段与 A 的媒体，且不含 B 的任何标记；
3. A 到期注销后：个人数据与媒体删除、官方视频保留、行为事件匿名化、收款流水
   脱敏、媒体清理队列全部 done、B 的文件不受影响；
4. 只读孤儿盘点脚本能识别故意留下的孤儿文件，且不删除任何东西。

证据写到 ``docs/evidence/iteration-3/a08-<日期>.json``。

.. note::
   这是 **2026-10** 的演练记录。2026-11 会员收费链路下线后，收款流水表
   （``jinshuju_payments``）、``orders`` 与导出/注销里的对应区段都已删除
   （迁移 ``d4e5f6a7b8c9``），因此本脚本不能直接重跑；现行"无收款数据"的
   导出与注销行为以 ``backend/tests/test_account_data.py`` 为准。
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"
COMPOSE_FILE = REPO_ROOT / "docker-compose.isolation.yml"
PROJECT = "seeword-isolation"
PG_PORT = int(os.environ.get("A08_PG_PORT", "15432"))

MEDIA_ROOT = Path(tempfile.gettempdir()) / "seeword-a08-media"

os.environ["ENV"] = "development"
os.environ["JWT_SECRET"] = "a08-isolation-secret-at-least-32-characters"
os.environ["DATABASE_URL"] = f"postgresql+asyncpg://seeword:isolation-only@127.0.0.1:{PG_PORT}/seeword_isolation"
os.environ["LOCAL_MEDIA_PATH"] = str(MEDIA_ROOT)
os.environ["REDIS_URL"] = "redis://127.0.0.1:16379/0"
os.environ["HEALTH_MONITOR_ENABLED"] = "false"

sys.path.insert(0, str(BACKEND_DIR))


def _docker_prefix() -> list[str]:
    if os.name == "nt":
        return ["wsl", "-d", os.environ.get("A08_WSL_DISTRO", "Ubuntu-24.04"), "--", "docker"]
    return ["docker"]


def _wsl_path(path: Path) -> str:
    if os.name != "nt":
        return str(path)
    drive, rest = os.path.splitdrive(str(path))
    return f"/mnt/{drive.rstrip(':').lower()}{rest.replace(os.sep, '/')}"


def compose(*args: str, check: bool = True) -> tuple[int, str, str]:
    base = [*_docker_prefix(), "compose", "-p", PROJECT]
    if os.name == "nt":
        base += ["--project-directory", _wsl_path(REPO_ROOT), "-f", _wsl_path(COMPOSE_FILE)]
    else:
        base += ["-f", str(COMPOSE_FILE)]
    proc = subprocess.run([*base, *args], capture_output=True, timeout=300, env=os.environ)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        raise RuntimeError(f"compose {' '.join(args)} failed: {out}\n{err}")
    return proc.returncode, out, err


def wait_pg(timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", PG_PORT), timeout=2):
                time.sleep(0.5)
                return
        except OSError as exc:
            last = exc
            time.sleep(0.5)
    raise TimeoutError(f"Postgres 未就绪: {last}")


async def seed(user_id: str, marker: str) -> dict:
    from sqlalchemy import select

    import app.models  # noqa: F401
    from app.core.database import async_session
    from app.models.behavior import BehaviorEvent
    from app.models.data_export import DataExportTask
    from app.models.exam_test import ExamAnswer, ExamSession
    from app.models.favorite import UserFavorite, UserNote
    from app.models.feedback import Feedback
    from app.models.jinshuju_payment import JinshujuPayment
    from app.models.learning import LearningRecord, Vocabulary
    from app.models.learning_plan import LearningEvent, UserLearningProfile
    from app.models.listening import ListeningSession
    from app.models.milestone import MasterySnapshot, UserMilestone
    from app.models.notification import Notification
    from app.models.order import Order
    from app.models.preferences import UserPreferences
    from app.models.study_session import StudySession, StudySessionItem
    from app.models.subtitle import Subtitle
    from app.models.user import User
    from app.models.video import Video
    from app.models.vocab_set import VocabSet, VocabSetWord

    now = datetime.now(UTC)
    async with async_session() as db:
        user = await db.get(User, user_id)
        assert user is not None
        user.avatar_url = f"/media/avatars/{marker}.png"

        video = Video(
            user_id=user_id,
            title=f"owned-{marker}",
            source_url=f"https://example.com/{marker}.mp4",
            is_official=False,
            video_url_720p=f"/media/{marker}_720p.mp4",
        )
        official = Video(
            user_id=user_id,
            title=f"official-{marker}",
            source_url=f"https://example.com/{marker}-official.mp4",
            is_official=True,
            is_published=True,
            video_url_720p=f"/media/official_{marker}_720p.mp4",
        )
        db.add_all([video, official])
        await db.flush()
        subtitle = Subtitle(video_id=video.id, sentence_index=0, start_time=0, end_time=1, text_en=marker)
        vocab = Vocabulary(user_id=user_id, word=f"word{marker}")
        db.add_all([subtitle, vocab])
        await db.flush()

        study = ExamSession(user_id=user_id, mode="paper_exam", question_count=1, started_at=now, score=1.0)
        db.add(study)
        await db.flush()
        db.add(
            ExamAnswer(session_id=study.id, question={"stem": marker}, user_answer="A", correct=True, answered_at=now)
        )
        listening = ListeningSession(user_id=user_id, video_id=video.id, title=f"listen-{marker}")
        session = StudySession(user_id=user_id, local_date=date.today(), target_count=1)
        vocab_set = VocabSet(user_id=user_id, video_id=video.id, exam_level="cet4")
        db.add_all([listening, session, vocab_set])
        await db.flush()
        db.add_all(
            [
                StudySessionItem(session_id=session.id, vocabulary_id=vocab.id, sort_order=1),
                VocabSetWord(set_id=vocab_set.id, vocabulary_id=vocab.id, position=1),
                LearningRecord(user_id=user_id, video_id=video.id, words_learned=1),
                LearningEvent(user_id=user_id, event_type="learned_words", event_value=1, event_date=date.today()),
                UserLearningProfile(user_id=user_id),
                UserPreferences(user_id=user_id),
                UserFavorite(user_id=user_id, video_id=video.id),
                UserNote(user_id=user_id, video_id=video.id, content=f"note-{marker}"),
                Order(user_id=user_id, order_number=f"ORD-{marker}", plan="pro_monthly", amount=1000),
                Notification(user_id=user_id, type="system", title=f"notify-{marker}"),
                Feedback(user_id=user_id, content=f"feedback-{marker}"),
                MasterySnapshot(user_id=user_id, snapshot_date=date.today(), mastery_json={"cet4": {"mastered": 1}}),
                UserMilestone(user_id=user_id, milestone_type=f"first-{marker}"),
                BehaviorEvent(user_id=user_id, event_type="watch_time", event_payload={"marker": marker}),
                JinshujuPayment(
                    entry_token=f"entry-{marker}",
                    serial_number=1,
                    form_token="form",
                    phone="13900000000",
                    amount_fen=1000,
                    status="applied",
                    user_id=user_id,
                    raw_json=f'{{"marker":"{marker}"}}',
                ),
                DataExportTask(user_id=user_id, status="pending"),
            ]
        )
        await db.commit()
        task = (
            (
                await db.execute(
                    select(DataExportTask)
                    .where(DataExportTask.user_id == user_id)
                    .order_by(DataExportTask.created_at.desc())
                )
            )
            .scalars()
            .first()
        )
        return {"video_id": video.id, "official_video_id": official.id, "task_id": task.id if task else None}


def write_media(user_id: str, marker: str, video_id: str) -> None:
    (MEDIA_ROOT / "avatars").mkdir(parents=True, exist_ok=True)
    (MEDIA_ROOT / "avatars" / f"{marker}.png").write_bytes(f"avatar-{marker}".encode())
    (MEDIA_ROOT / "shadowing" / user_id).mkdir(parents=True, exist_ok=True)
    (MEDIA_ROOT / "shadowing" / user_id / "rec.webm").write_bytes(f"rec-{marker}".encode())
    (MEDIA_ROOT / f"{marker}_720p.mp4").write_bytes(f"video-{marker}".encode())
    (MEDIA_ROOT / f"official_{marker}_720p.mp4").write_bytes(f"official-{marker}".encode())
    (MEDIA_ROOT / f"{video_id}_raw.mp4").write_bytes(f"raw-{marker}".encode())


async def run() -> dict:
    from sqlalchemy import func, select

    import app.models  # noqa: F401
    from app.core.database import Base, async_session, get_engine
    from app.models.behavior import BehaviorEvent
    from app.models.jinshuju_payment import JinshujuPayment
    from app.models.media_cleanup import MediaCleanupTask
    from app.models.user import User
    from app.models.video import Video
    from app.tasks.account_tasks import _build_export, _purge_due

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    alpha_id = str(uuid.uuid4())
    bravo_id = str(uuid.uuid4())
    async with async_session() as db:
        db.add_all(
            [
                User(id=alpha_id, phone="13800002001", name="Alpha"),
                User(id=bravo_id, phone="13800002002", name="Bravo"),
            ]
        )
        await db.commit()

    alpha = await seed(alpha_id, "alpha")
    bravo = await seed(bravo_id, "bravo")
    write_media(alpha_id, "alpha", alpha["video_id"])
    write_media(bravo_id, "bravo", bravo["video_id"])

    export_result = await _build_export(alpha["task_id"])
    async with async_session() as db:
        from app.models.data_export import DataExportTask

        task = await db.get(DataExportTask, alpha["task_id"])
        zip_rel = task.file_path if task else None
    zip_path = MEDIA_ROOT / zip_rel if zip_rel else None
    assert zip_path and zip_path.is_file(), "export ZIP missing"

    names: set[str]
    payloads: dict[str, str]
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        payloads = {name: zf.read(name).decode("utf-8", "replace") for name in names if name.endswith(".json")}
    combined = "\n".join(payloads.values())
    export_checks = {
        "sections_present": all(
            f"{section}.json" in names
            for section in (
                "profile",
                "preferences",
                "vocabulary",
                "favorites",
                "notes",
                "vocab_sets",
                "study_sessions",
                "listening_sessions",
                "exam_sessions",
                "orders",
                "payments",
                "behavior_events",
                "videos",
            )
        ),
        "alpha_payload": "note-alpha" in payloads.get("notes.json", ""),
        "no_bravo_rows": "bravo" not in combined and bravo_id not in combined,
        "avatar_included": "media/avatar/alpha.png" in names,
        "video_included": "media/videos/alpha_720p.mp4" in names,
        "shadowing_included": "media/shadowing/rec.webm" in names,
        "payment_without_raw_json": "raw_json" not in payloads.get("payments.json", ""),
    }

    async with async_session() as db:
        user = await db.get(User, alpha_id)
        assert user is not None
        user.deletion_scheduled_at = datetime.now(UTC) - timedelta(minutes=1)
        user.deletion_requested_at = datetime.now(UTC) - timedelta(days=31)
        await db.commit()
    purged = await _purge_due(now=datetime.now(UTC))

    async with async_session() as db:
        checks = {
            "purged_one": purged == 1,
            "alpha_gone": await db.get(User, alpha_id) is None,
            "bravo_kept": await db.get(User, bravo_id) is not None,
            "user_video_gone": await db.get(Video, alpha["video_id"]) is None,
            "official_video_kept": (await db.get(Video, alpha["official_video_id"])) is not None
            and (await db.get(Video, alpha["official_video_id"])).user_id is None,
            "behavior_anonymized": any(
                event.event_payload == {"marker": "alpha"}
                for event in (await db.execute(select(BehaviorEvent).where(BehaviorEvent.user_id.is_(None))))
                .scalars()
                .all()
            ),
            "payment_scrubbed": (
                await db.execute(select(JinshujuPayment).where(JinshujuPayment.entry_token == "entry-alpha"))
            )
            .scalar_one()
            .user_id
            is None,
            "cleanup_all_done": (
                await db.execute(select(func.count(MediaCleanupTask.id)).where(MediaCleanupTask.status == "pending"))
            ).scalar_one()
            == 0,
        }
        payment = (
            await db.execute(select(JinshujuPayment).where(JinshujuPayment.entry_token == "entry-alpha"))
        ).scalar_one()
        checks["payment_keeps_amount"] = payment.amount_fen == 1000
        checks["payment_phone_cleared"] = payment.phone is None and payment.raw_json is None

    files = {
        "alpha_avatar_gone": not (MEDIA_ROOT / "avatars" / "alpha.png").exists(),
        "alpha_shadowing_gone": not (MEDIA_ROOT / "shadowing" / alpha_id).exists(),
        "alpha_video_gone": not (MEDIA_ROOT / "alpha_720p.mp4").exists(),
        "official_media_kept": (MEDIA_ROOT / "official_alpha_720p.mp4").exists(),
        "alpha_raw_gone": not (MEDIA_ROOT / f"{alpha['video_id']}_raw.mp4").exists(),
        "alpha_export_dir_gone": not (MEDIA_ROOT / "exports" / alpha_id).exists(),
        "bravo_avatar_kept": (MEDIA_ROOT / "avatars" / "bravo.png").exists(),
        "bravo_video_kept": (MEDIA_ROOT / "bravo_720p.mp4").exists(),
    }

    # Read-only orphan inventory: drop one deliberately unreferenced file and
    # confirm the script reports it without deleting anything.
    orphan = MEDIA_ROOT / "orphan" / "junk.bin"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b"orphan")
    inventory = subprocess.run(
        [sys.executable, str(BACKEND_DIR / "scripts" / "inventory_orphan_media.py"), "--json"],
        capture_output=True,
        timeout=120,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    inventory_report = json.loads(inventory.stdout.decode("utf-8", "replace")) if inventory.returncode == 0 else {}
    inventory_checks = {
        "inventory_ran": inventory.returncode == 0,
        "orphan_detected": any(item["path"] == "orphan/junk.bin" for item in inventory_report.get("sample_orphans", []))
        or inventory_report.get("orphans_by_top_dir", {}).get("orphan", {}).get("files", 0) >= 1,
        "inventory_read_only": orphan.exists(),
    }

    await engine.dispose()

    return {
        "export": {"result": export_result, "checks": export_checks, "zip": str(zip_rel)},
        "purge": {"checks": checks, "files": files},
        "inventory": {"checks": inventory_checks, "report": inventory_report},
    }


def main() -> int:
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    compose("--profile", "pg", "down", "-v", check=False)
    compose("--profile", "pg", "up", "-d", "pg")
    wait_pg()
    try:
        result = asyncio.run(run())
    finally:
        compose("--profile", "pg", "down", "-v", check=False)

    checks = {
        **result["export"]["checks"],
        **result["purge"]["checks"],
        **result["purge"]["files"],
        **result["inventory"]["checks"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    evidence = {
        "task": "A08 / BE-04 account data export + deletion cleanup",
        "date": datetime.now(UTC).isoformat(),
        "environment": {"postgres": f"127.0.0.1:{PG_PORT}/seeword_isolation", "media_root": str(MEDIA_ROOT)},
        "checks": checks,
        "failed": failed,
        "detail": result,
    }
    out = REPO_ROOT / "docs" / "evidence" / "iteration-3" / f"a08-{date.today().isoformat()}.json"
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'} {name}")
    print(f"\n{len(checks) - len(failed)} passed / {len(failed)} failed — {out}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

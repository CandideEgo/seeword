"""Drive the whole SLCS publication workflow over real HTTP against one real Postgres.

Not a pytest test (it lives in ``backend/scripts/``): it boots the ASGI app on an
actual database that has been migrated to head, then walks the operator's path
end to end —

    import -> review -> sign a receipt with the CLI -> publish -> learner reads
    -> withdraw -> learner sees 410 with progress intact -> restore with a fresh
    receipt -> learner reads again

Why this exists next to ``tests/test_slcs_lessons.py``: that suite uses monkeypatched
keys and an in-process signer. This one calls ``scripts/sign_lesson_receipt.py`` as a
subprocess — the same binary an operator runs — so a drift between the signer's claims
and the site's verifier shows up here, not at the first real publication.

Run (working directory ``backend/``, Windows needs ``PYTHONUTF8=1``)::

    python scripts/smoke_lesson_publication.py \
        --database-url postgresql+asyncpg://user:pass@127.0.0.1:5432/slcs_drill

The database must already be at ``alembic upgrade head``; this script never migrates
and never deletes rows it did not create, so pointing it at a shared database only
adds a throwaway lesson (its ``lesson_id`` carries a random suffix).

Exit codes: 0 all checks passed, 1 a check failed or a step errored.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

REFERENCE = BACKEND.parent / "docs" / "slcs" / "examples" / "welcome-to-wikisource.json"

_results: list[bool] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    _results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail else ''}")
    return ok


def _signer(*args: str, database_url: str, key: Path, ttl: int = 600) -> subprocess.CompletedProcess[str]:
    """Run the operator's CLI exactly as documented, with the operator's key."""
    command = [
        sys.executable,
        str(BACKEND / "scripts" / "sign_lesson_receipt.py"),
        *args,
        "--database-url",
        database_url,
        "--private-key",
        str(key),
        "--issuer",
        "smoke-slcs-issuer",
        "--kid",
        "smoke",
        "--ttl",
        str(ttl),
    ]
    return subprocess.run(
        command,
        cwd=BACKEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
        timeout=120,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", required=True, help="已迁移到 head 的库（postgresql+asyncpg://…）")
    args = parser.parse_args()

    # Settings reads DATABASE_URL at import time; set it before importing app.*.
    os.environ["DATABASE_URL"] = args.database_url
    os.environ.setdefault("PYTHONUTF8", "1")

    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import select

    from app.core.config import get_settings
    from app.core.database import get_async_session_maker
    from app.core.security import create_token
    from app.main import app
    from app.models.lesson import Lesson, LessonRevision
    from app.models.user import RoleType, User

    settings = get_settings()

    # One throwaway keypair, outside the repository, used only by this run.
    keydir = Path(tempfile.mkdtemp(prefix="slcs-smoke-key-"))
    key = keydir / "signing.pem"
    generated = subprocess.run(
        [
            sys.executable,
            str(BACKEND / "scripts" / "sign_lesson_receipt.py"),
            "keygen",
            "--out",
            str(key),
            "--issuer",
            "smoke-slcs-issuer",
            "--kid",
            "smoke",
        ],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if generated.returncode != 0:
        print(generated.stderr)
        return 1
    public_pem = json.loads(generated.stderr.split("SLCS_LESSON_RECEIPT_PUBLIC_KEYS=")[1].split("\n")[0])["smoke"]

    # Turn the pilot on for this process only; the receipt keys are what the
    # operator would have written into backend/.env.
    object.__setattr__(settings, "slcs_lessons_enabled", True)
    object.__setattr__(settings, "slcs_vocabulary_enabled", True)
    object.__setattr__(settings, "slcs_lesson_receipt_issuer", "smoke-slcs-issuer")
    object.__setattr__(settings, "slcs_lesson_receipt_public_keys", {"smoke": public_pem})
    object.__setattr__(settings, "slcs_lesson_receipt_max_age_seconds", 900)

    suffix = uuid.uuid4().hex[:8]
    lesson_id = f"smoke-lesson-{suffix}"
    document = json.loads(REFERENCE.read_text(encoding="utf-8"))
    document["lesson_id"] = lesson_id
    pack_json = json.dumps(document, ensure_ascii=False)

    async with get_async_session_maker()() as db:
        admin = User(phone=f"1390000{suffix[:4]}", hashed_password="x", role=RoleType.admin)
        learner = User(phone=f"1390001{suffix[:4]}", hashed_password="x", role=RoleType.user, onboarding_completed=True)
        db.add_all([admin, learner])
        await db.flush()
        admin_id, learner_id = admin.id, learner.id
        await db.commit()

    admin_headers = {"Authorization": f"Bearer {create_token(admin_id)}"}
    learner_headers = {"Authorization": f"Bearer {create_token(learner_id)}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://smoke", timeout=60) as c:
        print("\n[1] 导入候选修订")
        r = await c.post(
            "/api/v1/admin/lessons/import",
            headers=admin_headers,
            json={"operation_id": f"import-{suffix}", "pack_json": pack_json},
        )
        check("导入 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")
        if r.status_code != 200:
            return 1
        detail = r.json()
        revision_id = detail["revision_id"]
        fingerprint = detail["fingerprint"]
        check("候选状态", detail["status"] == "candidate", detail["status"])
        # The drill rewrites lesson_id, so this is *not* REFERENCE_DIGEST. What must
        # hold is that the same bytes fingerprint the same way every time.
        again = await c.post(
            "/api/v1/admin/lessons/import",
            headers=admin_headers,
            json={"operation_id": f"import-again-{suffix}", "pack_json": pack_json},
        )
        check(
            "同一包重复导入得到同一修订同一指纹",
            again.status_code == 200
            and again.json()["revision_id"] == revision_id
            and again.json()["fingerprint"] == fingerprint,
            f"status={again.status_code}",
        )

        print("\n[2] 候选版对学习者不可见")
        r = await c.get(f"/api/v1/lessons/{lesson_id}", headers=learner_headers)
        check("未发布 404", r.status_code == 404, f"status={r.status_code}")

        print("\n[3] 未审核时发布被拒")
        early = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            revision_id,
            database_url=args.database_url,
            key=key,
        )
        check(
            "签发方拒绝未审核修订", early.returncode == 1, early.stderr.strip().splitlines()[-1] if early.stderr else ""
        )

        print("\n[4] 维护者审核（站内展示 + 模型处理）")
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/review",
            headers=admin_headers,
            json={
                "operation_id": f"review-{suffix}",
                "source_commit": "0" * 40,
                "uses": {
                    "site_display": {"approved": True, "evidence": "CC BY-SA 4.0，署名与出处随包"},
                    "model_processing": {"approved": True, "evidence": "同一许可，仅站内导师"},
                    "external_redistribution": {"approved": False, "evidence": "未获准再分发"},
                },
            },
        )
        check("审核 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")
        review_hash = r.json()["review"]["review_sha256"]

        print("\n[5] 用签发方 CLI 生成收据（子进程，走真实 CLI）")
        signed = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            revision_id,
            database_url=args.database_url,
            key=key,
        )
        check("签发 exit 0", signed.returncode == 0, signed.stderr.strip()[-300:])
        token = signed.stdout.strip()
        check("stdout 只有一行 JWT", "\n" not in token and token.count(".") == 2)
        check(
            "摘要里有审核哈希",
            review_hash[:12] in signed.stderr,
            signed.stderr.splitlines()[4] if len(signed.stderr.splitlines()) > 4 else "",
        )

        print("\n[6] 发布")
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={"operation_id": f"publish-{suffix}", "expected_current_revision_id": None, "receipt": token},
        )
        check("发布 200", r.status_code == 200, f"status={r.status_code} {r.text[:300]}")
        if r.status_code != 200:
            return 1
        check("状态 published", r.json()["status"] == "published")

        print("\n[7] 学习者现在能读")
        r = await c.get(f"/api/v1/lessons/{lesson_id}", headers=learner_headers)
        check("读取 200", r.status_code == 200, f"status={r.status_code}")
        body = r.json()
        check("12 段字幕", len(body["pack"]["segments"]) == 12, f"n={len(body['pack']['segments'])}")
        check(
            "目录里出现",
            lesson_id
            in {
                item["lesson_id"]
                for item in (await c.get("/api/v1/lessons", headers=learner_headers)).json()["lessons"]
            },
        )

        print("\n[9] 保存进度")
        r = await c.put(
            f"/api/v1/lessons/{lesson_id}/progress",
            headers=learner_headers,
            json={"revision_id": revision_id, "position_ms": 13_000},
        )
        check("进度 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")

        print("\n[10] 撤回")
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/withdraw",
            headers=admin_headers,
            json={"operation_id": f"withdraw-{suffix}", "reason": "演练：核对撤回即时生效"},
        )
        check("撤回 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")

        print("\n[11] 撤回后：正文不可读、进度仍在、目录隐藏")
        r = await c.get(f"/api/v1/lessons/{lesson_id}", headers=learner_headers)
        check("课程 410", r.status_code == 410, f"status={r.status_code}")
        r = await c.get(f"/api/v1/lessons/{lesson_id}/progress", headers=learner_headers)
        check("进度仍 200", r.status_code == 200, f"status={r.status_code}")
        r = await c.get("/api/v1/lessons", headers=learner_headers)
        check("目录已隐藏", lesson_id not in {item["lesson_id"] for item in r.json()["lessons"]})

        print("\n[12] 用新收据恢复发布")
        restored = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            revision_id,
            database_url=args.database_url,
            key=key,
        )
        check("再次签发 exit 0", restored.returncode == 0, restored.stderr.strip()[-200:])
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"restore-{suffix}",
                "expected_current_revision_id": None,
                "receipt": restored.stdout.strip(),
            },
        )
        check("恢复 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")

        print("\n[12b] 已用过的收据不能再发布（唯一约束，不是「已是当前版」）")
        # Withdraw first: otherwise every publish attempt short-circuits on
        # "already the current revision" *before* the receipt is verified, and a
        # check here would pass no matter what the replay guard did.
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/withdraw",
            headers=admin_headers,
            json={"operation_id": f"withdraw-replay-{suffix}", "reason": "演练：重放检查"},
        )
        check("为重放检查再撤回 200", r.status_code == 200, f"status={r.status_code}")
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"replay-{suffix}",
                "expected_current_revision_id": None,
                "receipt": restored.stdout.strip(),
            },
        )
        check(
            "重放同一收据被拒 409 IDEMPOTENCY_CONFLICT",
            r.status_code == 409 and r.json().get("code") == "IDEMPOTENCY_CONFLICT",
            f"status={r.status_code} {r.text[:200]}",
        )
        # Put it back so the later steps still see a published revision.
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"restore-again-{suffix}",
                "expected_current_revision_id": None,
                "receipt": _signer(
                    "sign",
                    "--lesson-id",
                    lesson_id,
                    "--revision-id",
                    revision_id,
                    database_url=args.database_url,
                    key=key,
                ).stdout.strip(),
            },
        )
        check("用全新收据恢复 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")

        print("\n[13] 恢复后正文与进度都在")
        r = await c.get(f"/api/v1/lessons/{lesson_id}", headers=learner_headers)
        check("课程 200", r.status_code == 200, f"status={r.status_code}")
        r = await c.get(f"/api/v1/lessons/{lesson_id}/progress", headers=learner_headers)
        check("进度保留", r.status_code == 200 and r.json().get("position_ms") == 13_000, r.text[:160])

        print("\n[14] 超出站点上限的收据被拒")
        # The signer caps --ttl at 86400 and the site caps the *window* at
        # SLCS_LESSON_RECEIPT_MAX_AGE_SECONDS (900 here), so a 901 s receipt is a
        # well-formed token the site must still refuse.
        await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/withdraw",
            headers=admin_headers,
            json={"operation_id": f"withdraw2-{suffix}", "reason": "演练：超长有效期收据"},
        )
        long_lived = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            revision_id,
            database_url=args.database_url,
            key=key,
            ttl=901,
        )
        check("签发方允许 901s（站点上限是另一回事）", long_lived.returncode == 0, long_lived.stderr.strip()[-200:])
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"toolong-{suffix}",
                "expected_current_revision_id": None,
                "receipt": long_lived.stdout.strip(),
            },
        )
        check("超出上限被拒 422", r.status_code == 422, f"status={r.status_code} {r.text[:160]}")

        print("\n[15] 篡改声明后签名失效")
        good = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            revision_id,
            database_url=args.database_url,
            key=key,
        )
        header, payload, signature = good.stdout.strip().split(".")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        claims["receipt"]["fingerprint"] = "0" * 64
        tampered = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"tampered-{suffix}",
                "expected_current_revision_id": None,
                "receipt": f"{header}.{tampered}.{signature}",
            },
        )
        check("篡改被拒 422", r.status_code == 422, f"status={r.status_code} {r.text[:160]}")

        print("\n[16] 回退到被取代的旧修订（这是第三条要收据的发布路径）")
        # Publish a second, different revision so the first one becomes a
        # *superseded published* revision, then sign a receipt for it. The site
        # accepts this (publish_lesson only refuses the current revision), and
        # the admin page offers the form, so the signer must be able to mint it.
        second = json.loads(REFERENCE.read_text(encoding="utf-8"))
        second["lesson_id"] = lesson_id
        second["title"] = "Welcome to Wikisource（浏览器验收 · 第二版）"
        r = await c.post(
            "/api/v1/admin/lessons/import",
            headers=admin_headers,
            json={"operation_id": f"import2-{suffix}", "pack_json": json.dumps(second, ensure_ascii=False)},
        )
        check("第二版导入 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")
        second_id = r.json()["revision_id"]
        check("第二版是新修订", second_id != revision_id, f"{second_id} vs {revision_id}")
        await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{second_id}/review",
            headers=admin_headers,
            json={
                "operation_id": f"review2-{suffix}",
                "source_commit": "0" * 40,
                "uses": {
                    "site_display": {"approved": True, "evidence": "同第一版"},
                    "model_processing": {"approved": True, "evidence": "同第一版"},
                    "external_redistribution": {"approved": False, "evidence": "未获准再分发"},
                },
            },
        )
        # Steps [14] left the lesson withdrawn, so its current revision is None.
        # Read it back rather than assuming: this is exactly the value the
        # compare-and-swap in publish_lesson checks.
        r = await c.get("/api/v1/admin/lessons", headers=admin_headers)
        current = next(item["current_revision_id"] for item in r.json()["lessons"] if item["lesson_id"] == lesson_id)
        print(f"  课程当前版：{current}")
        signer_for_second = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            second_id,
            database_url=args.database_url,
            key=key,
        )
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{second_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"publish2-{suffix}",
                "expected_current_revision_id": current,
                "receipt": signer_for_second.stdout.strip(),
            },
        )
        check("第二版发布 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")

        # ``revision_id`` is now published-but-superseded. Omitting
        # --revision-id must find it (it is not the current revision).
        rollback_receipt = _signer(
            "sign",
            "--lesson-id",
            lesson_id,
            "--revision-id",
            revision_id,
            database_url=args.database_url,
            key=key,
        )
        check(
            "签发方能为被取代的修订签收据",
            rollback_receipt.returncode == 0,
            rollback_receipt.stderr.strip()[-200:],
        )
        r = await c.post(
            f"/api/v1/admin/lessons/{lesson_id}/revisions/{revision_id}/publish",
            headers=admin_headers,
            json={
                "operation_id": f"rollback-{suffix}",
                "expected_current_revision_id": second_id,
                "receipt": rollback_receipt.stdout.strip(),
            },
        )
        check("回退发布 200", r.status_code == 200, f"status={r.status_code} {r.text[:200]}")
        check("回退后当前版是旧修订", (r.json().get("revision_id") if r.status_code == 200 else None) == revision_id)

    async with get_async_session_maker()() as db:
        rows = (await db.execute(select(LessonRevision).where(LessonRevision.lesson_id == lesson_id))).scalars().all()
        check("整套演练只产生两个修订", len(rows) == 2, f"n={len(rows)}")
        lesson = await db.get(Lesson, lesson_id)
        check("当前版指针指向被回退到的旧修订", lesson is not None and lesson.current_revision_id == revision_id)

    await _cleanup(lesson_id, admin_id, learner_id, keydir)
    print(f"\n{'=' * 60}\n冒烟结果：{sum(_results)}/{len(_results)} 通过")
    if all(_results):
        print(
            "课程发布全链路通过：导入 → 审核 → CLI 签收据 → 发布 → 学习 → 撤回 → 恢复 → "
            "拒收重放/超限/篡改 → 回退到被取代的修订"
        )
        return 0
    print("存在失败项，见上方 [FAIL]")
    return 1


async def _cleanup(lesson_id: str, admin_id: str, learner_id: str, keydir: Path) -> None:
    """Remove what this run created, so pointing it at a shared DB leaves nothing.

    The drill needs two accounts (one admin) to drive the real endpoints, and it
    mints a throwaway signing key. Leaving either behind is not acceptable on a
    database other people use: a stray ``role=admin`` row with an unusable
    password hash answers 500 instead of 401 on login.

    Every lesson foreign key is ``ON DELETE RESTRICT`` and ``lessons`` points at
    ``lesson_revisions`` and vice versa, so deletion is ordered and the cycle is
    broken first. Rows the drill created itself (progress, activities, sources)
    are the drill's to remove; the script never touched another lesson.
    """
    import shutil

    from sqlalchemy import delete, select, text

    from app.core.database import get_async_session_maker
    from app.models.lesson import Lesson, LessonOperation, LessonRevision
    from app.models.user import User

    shutil.rmtree(keydir, ignore_errors=True)
    print(f"\n[清理] 已删除临时签发密钥目录 {keydir}")

    revision_ids = select(LessonRevision.id).where(LessonRevision.lesson_id == lesson_id)
    try:
        async with get_async_session_maker()() as db:
            # Break the lessons <-> lesson_revisions cycle before deleting either.
            await db.execute(
                text("UPDATE lessons SET current_revision_id = NULL WHERE id = :lesson_id"), {"lesson_id": lesson_id}
            )
            for table in (
                "lesson_tutor_anchors",
                "lesson_vocabulary_sources",
                "lesson_activities",
            ):
                # These hang off the revision, not the lesson. ``lesson_progress``
                # is the one keyed on lesson_id and is deleted separately.
                await db.execute(
                    text(
                        f"DELETE FROM {table} WHERE revision_id IN "
                        "(SELECT id FROM lesson_revisions WHERE lesson_id = :lesson_id)"
                    ),
                    {"lesson_id": lesson_id},
                )
            await db.execute(text("DELETE FROM lesson_progress WHERE lesson_id = :lesson_id"), {"lesson_id": lesson_id})
            await db.execute(delete(LessonOperation).where(LessonOperation.revision_id.in_(revision_ids)))
            await db.execute(delete(LessonRevision).where(LessonRevision.lesson_id == lesson_id))
            await db.execute(delete(Lesson).where(Lesson.id == lesson_id))
            await db.execute(delete(User).where(User.id.in_([admin_id, learner_id])))
            await db.commit()
        print("[清理] 已删除演练课程、它的学习记录与两个临时账号")
    except Exception as exc:
        print(f"[清理] 未能清理（{type(exc).__name__}: {exc}）：课程 {lesson_id}、账号 {admin_id}/{learner_id}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

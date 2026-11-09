"""Seed four verified questions plus a teaching grant, for local walkthroughs.

Dev-only counterpart of ``tests/teaching_fixtures.py``: it reuses the *same*
synthetic candidate builder instead of keeping a copy, so the material the
browser walkthrough exercises is the material the tests exercise. The content is
not real exam material — the receipt verifier is a stub — so nothing seeded
here may be described as qualified teaching content.

It imports ``tests.teaching_fixtures``, which exists only in a source checkout;
that is deliberate, this script never runs in a deployed image.

Usage (working directory ``backend/``, ``PYTHONUTF8=1`` on Windows):

    python scripts/seed_teaching_quiz.py --phone 13800138000
    python scripts/seed_teaching_quiz.py --phone 13800138000 --reset

``--reset`` deletes the previously seeded paper (and its revisions) first, so a
second run after editing the fixture does not stack duplicates. Exits 0 on
success, 1 on lookup / validation error.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Run as `python scripts/<name>.py` from `backend/`: that puts `scripts/` on
# sys.path, not the backend root, so `app.*` and `tests.*` would not resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select
from tests.teaching_fixtures import QUIZ_QUESTIONS, original_candidate

from app.core.database import async_session
from app.models.exam_test import ExamPaper, ExamQuestion
from app.models.question_exposure import UserExposureMappingState
from app.models.teaching import ExamAnalysisRevision
from app.models.user import User
from app.models.v2_runtime import TeachingAccessGrant
from app.services.teaching.content import publish_revision

# A free identity tuple in any seeded database, and the one the fixture payload
# uses: ``publish_revision`` re-checks the fingerprint against the live question
# row, so the paper identity and the payload identity must agree.
PAPER_KEY = {"level": "cet4", "year": 2024, "month": 12, "set_no": 3}
PAYLOAD_IDENTITY = {"year": 2024, "month": 12}


async def _verifier(_receipt: dict) -> bool:
    # Dev seeding only: real publication requires real signed receipts.
    return True


def _paper_match() -> list:
    return [getattr(ExamPaper, key) == value for key, value in PAPER_KEY.items()]


async def _reset(db) -> None:
    question_ids = (
        (
            await db.execute(
                select(ExamQuestion.id).join(ExamPaper, ExamPaper.id == ExamQuestion.paper_id).where(*_paper_match())
            )
        )
        .scalars()
        .all()
    )
    if question_ids:
        await db.execute(delete(ExamAnalysisRevision).where(ExamAnalysisRevision.question_id.in_(question_ids)))
    for paper in (await db.execute(select(ExamPaper).where(*_paper_match()))).scalars().all():
        await db.execute(delete(ExamQuestion).where(ExamQuestion.paper_id == paper.id))
        await db.delete(paper)
    await db.commit()


async def _seed(phone: str, reset: bool) -> int:
    async with async_session() as db:
        user = await db.scalar(select(User).where(User.phone == phone))
        if user is None:
            raise LookupError(f"没有手机号为 {phone} 的账号；先注册或先跑 seed_e2e.py")
        if reset:
            await _reset(db)
        existing = (await db.execute(select(ExamPaper.id).where(*_paper_match()))).scalar_one_or_none()
        if existing is not None:
            print(f"该卷已存在（paper {existing}）；要重新播种请加 --reset")
            return 0

        paper = ExamPaper(
            **PAPER_KEY,
            title="Synthetic quiz walking fixture",
            source="seed_teaching_quiz.py (synthetic, not exam content)",
            total_questions=len(QUIZ_QUESTIONS),
        )
        db.add(paper)
        await db.flush()

        for offset, question_text in enumerate(QUIZ_QUESTIONS):
            candidate = original_candidate(
                number=46 + offset, question=question_text, **PAYLOAD_IDENTITY, set_no=PAPER_KEY["set_no"]
            )
            payload = candidate["question_payload"]
            question = ExamQuestion(
                paper_id=paper.id,
                section="reading_C",
                number=payload["number"],
                question_type="reading",
                passage=payload["passage"],
                question=payload["question"],
                options=payload["options"],
                answer=candidate["correct_answer"],
            )
            db.add(question)
            await db.flush()
            candidate["question_id"] = question.id
            await publish_revision(db, candidate, verify_receipt=_verifier)

        if (await db.get(UserExposureMappingState, user.id)) is None:
            db.add(UserExposureMappingState(user_id=user.id, status="complete"))
        if (await db.get(TeachingAccessGrant, user.id)) is None:
            db.add(TeachingAccessGrant(user_id=user.id))
        await db.commit()
        print(f"已为 {phone} 播种 {len(QUIZ_QUESTIONS)} 道合成题目（paper {paper.id}）并授予教学访问")
        print("提示：这是合成素材，不是真题；需要 TEACHING_ENABLED=true 才能看到入口")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="播种合成教学小测并授予教学访问（仅本机开发用）")
    parser.add_argument("--phone", required=True, help="要授权的账号手机号")
    parser.add_argument("--reset", action="store_true", help="先删除上次播种的同卷题目")
    args = parser.parse_args(argv)
    try:
        return asyncio.run(_seed(args.phone, args.reset))
    except LookupError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Import standardized 真题 JSON (data/papers/*.json) into the exam bank.

For each record {level, year, month, set_no, title, source, questions[]}:
  * upsert ``exam_papers`` (key: level/year/month/set_no)
  * upsert ``exam_questions`` (key: paper_id/number) — updates passage/
    question/options/answer/explanation when the source changed
  * syncs reading passages into ``exam_sentences`` (the word-card gloss
    corpus) via ``app.services.exam_corpus.ingest_sentences`` so gloss
    lookups also get real 真题 sentences.

Usage:
    cd backend
    python scripts/import_exam_papers.py data/papers/papers_cet4.json
    python scripts/import_exam_papers.py data/papers/            # all *.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.core.database import async_session
from app.models.exam_test import ExamPaper, ExamQuestion
from app.services import exam_corpus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Split a passage into sentences on . / ! / ? boundaries (same as the legacy
# exam-corpus ETL).
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Fields copied onto each question row.
_Q_FIELDS = ("section", "number", "passage", "question", "options", "answer", "explanation", "question_type")


async def _upsert_paper(db: AsyncSession, rec: dict) -> ExamPaper:
    stmt = select(ExamPaper).where(
        ExamPaper.level == rec["level"],
        ExamPaper.year == rec["year"],
        ExamPaper.month == rec["month"],
        ExamPaper.set_no == rec["set_no"],
    )
    paper = (await db.execute(stmt)).scalar_one_or_none()
    if paper is None:
        paper = ExamPaper(
            level=rec["level"],
            year=rec["year"],
            month=rec["month"],
            set_no=rec["set_no"],
            title=rec["title"],
            source=rec.get("source"),
            total_questions=len(rec["questions"]),
        )
        db.add(paper)
        await db.flush()
    else:
        paper.title = rec["title"]
        paper.source = rec.get("source")
        paper.total_questions = len(rec["questions"])
    return paper


async def _upsert_questions(db: AsyncSession, paper: ExamPaper, rec: dict) -> int:
    existing = {
        q.number: q for q in (await db.execute(select(ExamQuestion).where(ExamQuestion.paper_id == paper.id))).scalars()
    }
    for qdata in rec["questions"]:
        q = existing.get(int(qdata["number"]))
        if q is None:
            q = ExamQuestion(paper_id=paper.id)
            db.add(q)
        for field in _Q_FIELDS:
            setattr(q, field, qdata.get(field))
    # Remove questions that no longer exist in the source.
    keep = {int(q["number"]) for q in rec["questions"]}
    for num, q in existing.items():
        if num not in keep:
            await db.delete(q)
    return len(rec["questions"])


# 试卷科目（展示侧见 frontend/src/lib/examSubjects.ts）与词汇大纲等级
# （app.core.exam_levels）是两套：
# 考研题库按英语一/英语二拆成 ky1/ky2，但真题语料的等级键必须是 ECDICT 词表用的 ky，
# 否则 find_example_sentence(levels=["ky"]) 永远匹配不到这些句子（句子会变成死行）。
_CORPUS_LEVEL = {"ky1": "ky", "ky2": "ky"}


async def _sync_exam_sentences(db: AsyncSession, rec: dict) -> int:
    """Push reading-passage sentences into the word-card gloss corpus."""
    level = _CORPUS_LEVEL.get(rec["level"], rec["level"])
    year = rec["year"]
    month = rec["month"]
    # 归属直接用卷名：cet4/ky1/ky2 的 set_no 与月份口径各不相同，拼出来的
    # 「2016年12月KY1真题（第1套）」既难看又和 ky2 撞车。
    source = rec["title"]
    records: list[dict] = []
    for q in rec["questions"]:
        passage = (q.get("passage") or "").strip()
        if not passage:
            continue
        # Strip the [word bank] appendix from cloze passages.
        if "[word bank]" in passage:
            passage = passage.split("[word bank]")[0].strip()
        for sent in (s.strip() for s in _SENTENCE_SPLIT_RE.split(passage) if s.strip()):
            records.append(
                {
                    "level": level,
                    "year": year,
                    "month": month,
                    "question_type": "reading",
                    "sentence_en": sent,
                    "sentence_zh": None,
                    "source": source,
                }
            )
    if not records:
        return 0
    inserted, _levels = await exam_corpus.ingest_sentences(db, records)
    return inserted


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="JSON file or directory of .json files")
    parser.add_argument("--dry-run", action="store_true", help="parse only, no DB writes")
    parser.add_argument("--no-sentences", action="store_true", help="skip exam_sentences sync")
    args = parser.parse_args()

    src = Path(args.path)
    files = sorted(src.glob("*.json")) if src.is_dir() else [src]
    if not src.exists():
        print(f"[error] path not found: {src}", file=sys.stderr)
        return 1

    records: list[dict] = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[error] failed to parse {f}: {e}", file=sys.stderr)
            continue
        records.extend(data if isinstance(data, list) else [data])
    print(f"[parse] {len(files)} file(s), {len(records)} paper records")

    if args.dry_run:
        qs = sum(len(r["questions"]) for r in records)
        print(f"[dry-run] would import {len(records)} papers / {qs} questions")
        return 0

    async with async_session() as db:
        for rec in records:
            paper = await _upsert_paper(db, rec)
            q_count = await _upsert_questions(db, paper, rec)
            print(f"[ok] {rec['level']} {rec['year']}-{rec['month']} 第{rec['set_no']}套: {q_count} questions")
        await db.flush()
        if not args.no_sentences:
            sent_total = 0
            for rec in records:
                sent_total += await _sync_exam_sentences(db, rec)
            print(f"[sentences] {sent_total} new 真题 sentences synced to exam_sentences")
        await db.commit()
    print("[done] import complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

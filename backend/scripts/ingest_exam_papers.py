#!/usr/bin/env python
"""Ingest 真题 (past-paper) sentences into the exam corpus.

Reads a JSON file (or a directory of .json files) of standardized 真题 records
and populates ``exam_sentences`` / ``exam_sentence_words`` / ``exam_word_freq``
via ``app.services.exam_corpus.ingest_sentences``.

Standard input format — a JSON array of records:
    [
      {
        "level": "cet6",                 # canonical level key (cet4/cet6/ky/gaoKao/...)
        "year": 2018,                     # optional
        "month": 12,                      # optional (6 or 12)
        "question_type": "reading",       # optional (reading/listening/cloze/...)
        "sentence_en": "...",             # required
        "sentence_zh": "...",             # optional
        "source": "2018年12月六级真题"     # optional provenance
      },
      ...
    ]

If a record's "sentence_en" is a multi-sentence paragraph, it is split into
individual sentences before ingest.

USAGE / DATA SOURCE:
  This is the integration point for real 真题 data. The actual past-paper
  corpus (which GitHub repo / licensed dataset) is TBD — point this script at
  a converted JSON file matching the schema above. A small tracked example
  lives at ``backend/tests/fixtures/example_exam_sentences.json`` for
  smoke-testing (``backend/data/`` is gitignored, so the example cannot live
  there).

Usage:
    cd backend
    python scripts/ingest_exam_papers.py tests/fixtures/example_exam_sentences.json
    python scripts/ingest_exam_papers.py data/papers/   # directory of .json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session
from app.models.exam_corpus import ExamSentence
from app.services import ecdict, exam_corpus

# Split a paragraph into sentences on . / ! / ? boundaries, keeping it simple.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Fields allowed in a record; extras are ignored.
ALLOWED_FIELDS = {
    "level",
    "year",
    "month",
    "question_type",
    "sentence_en",
    "sentence_zh",
    "source",
}


def _normalize_record(rec: dict) -> list[dict]:
    """Validate one record and split multi-sentence English text into rows."""
    if not isinstance(rec, dict):
        return []
    en = str(rec.get("sentence_en") or "").strip()
    level = str(rec.get("level") or "").strip()
    if not en or not level:
        return []
    base = {k: rec.get(k) for k in ALLOWED_FIELDS}
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(en) if s.strip()]
    if len(sentences) <= 1:
        return [base]
    # Multi-sentence: only the (zh) translation attaches to the first chunk.
    out = []
    for i, s in enumerate(sentences):
        row = dict(base)
        row["sentence_en"] = s
        if i > 0:
            row["sentence_zh"] = None
        out.append(row)
    return out


def _load_records(path: Path) -> list[dict]:
    """Load JSON records from a file or a directory of .json files."""
    records: list[dict] = []
    files = []
    if path.is_dir():
        files = sorted(path.glob("*.json"))
    else:
        files = [path]
    if not files:
        print(f"[error] no JSON files found at {path}", file=sys.stderr)
        return records
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[error] failed to parse {f}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            data = [data]
        if isinstance(data, list):
            records.extend(data)
    return records


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="JSON file or directory of .json files")
    parser.add_argument("--dry-run", action="store_true", help="parse and validate only, no DB writes")
    args = parser.parse_args()

    if not ecdict.is_available():
        print(
            f"[warn] ECDICT db not found at {ecdict.DB_PATH} — sentences will be ingested "
            "but the word index will be empty. Run: python scripts/download_ecdict.py",
            file=sys.stderr,
        )

    src = Path(args.path)
    if not src.exists():
        print(f"[error] path not found: {src}", file=sys.stderr)
        return 1

    raw = _load_records(src)
    normalized: list[dict] = []
    for rec in raw:
        normalized.extend(_normalize_record(rec))
    print(f"[parse] {len(raw)} raw records -> {len(normalized)} sentence rows")

    if args.dry_run:
        for r in normalized[:10]:
            print(f"  [{r.get('level')}] {r.get('sentence_en')[:80]}")
        if len(normalized) > 10:
            print(f"  ... ({len(normalized) - 10} more)")
        print("[dry-run] no DB writes")
        return 0

    async with async_session() as db:
        # Pre-count for reporting.
        before = (await db.execute(select(ExamSentence.id))).all()
        inserted, levels = await exam_corpus.ingest_sentences(db, normalized)
    print(f"[done] ingested {inserted} new sentences, levels touched: {sorted(levels)}")
    print(f"[done] corpus now has {len(before) + inserted} sentences total")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

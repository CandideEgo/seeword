#!/usr/bin/env python
"""把抓下来的原卷 PDF 收成站内可下载的一份清单 + 一个目录。

源：``~/guojiya/pdf_index.json``（206 条，字段 ``title`` /
``show_title`` / ``file_path`` / ``pdf_url`` / ``bytes`` / ``sha256`` / ``section`` /
``slug`` / ``file``）与它指向的 ``pdf/<section>/<slug>.pdf``。

产出：

    backend/data/exam_pdfs/
      index.json                 # 裁剪版清单（不含 pdf_url，那是抓取侧的账）
      files/<slug>.pdf           # 206 份，逐份校验 sha256

**为什么不放进 ``data/papers/``**：``import_exam_papers.py`` 的 ``src.glob("*.json")``
会把同目录的清单当试卷读进去，然后在 ``rec["level"]`` 上 KeyError。

**这些文件不进镜像、不进 git**：``backend/data/`` 在 ``.gitignore`` 与
``backend/.dockerignore`` 里，生产靠 ``./backend/data:/app/data:ro`` 只读 bind mount，
所以要人工同步（部署清单里的 D2）。

用法：

    cd backend
    python scripts/build_exam_pdf_index.py            # 复制 + 校验
    python scripts/build_exam_pdf_index.py --check-only   # 只校验现有产物
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

DEFAULT_SRC = Path.home() / "guojiya"
DEFAULT_OUT = Path("data/exam_pdfs")

# 科目排序（只用于本脚本的输出顺序；展示名与排序的唯一事实源是
# frontend/src/lib/examSubjects.ts）。
SUBJECT_ORDER = {"cet4": 1, "cet6": 2, "kaoyan": 5, "tem4": 6, "tem8": 7}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def split_slot(file_path: str) -> tuple[int, int | None, int]:
    """``cet4/2014-06/01`` → (2014, 6, 1)；``kaoyan/2000/01`` → (2000, None, 1)。

    考研与专四专八的路径里没有月份段，最后一段对考研来说是「卷种」（01=英语一 /
    02=英语二 / 03=…），对专四专八来说没有意义 —— 一律按原样落到 set_no，
    界面上只用 year 排序，别给它加含义。
    """
    parts = file_path.split("/")
    year = int(parts[1][:4])
    month = int(parts[1][5:7]) if "-" in parts[1] else None
    set_no = int(parts[2]) if len(parts) > 2 else 0
    return year, month, set_no


def build_records(src_index: dict) -> list[dict]:
    out = []
    for p in src_index["papers"]:
        year, month, set_no = split_slot(p["file_path"])
        out.append(
            {
                "slug": p["slug"],
                "title": p["title"],
                "subject": p["section"],
                "year": year,
                "month": month,
                "set_no": set_no,
                "bytes": p["bytes"],
                "sha256": p["sha256"],
                "rel_path": f"files/{p['slug']}.pdf",
                "_src": p["file"],
            }
        )
    out.sort(key=lambda r: (SUBJECT_ORDER.get(r["subject"], 99), -r["year"], -(r["month"] or 0), r["set_no"]))
    slugs = [r["slug"] for r in out]
    assert len(set(slugs)) == len(slugs), "slug 有重复"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--check-only", action="store_true", help="不复制、不写清单，只校验")
    args = ap.parse_args()

    src_index_path = args.src / "pdf_index.json"
    if not src_index_path.is_file():
        print(f"[error] 找不到 {src_index_path}", file=sys.stderr)
        return 1
    records = build_records(json.loads(src_index_path.read_text(encoding="utf-8")))
    files_dir = args.out / "files"

    if args.check_only:
        bad = []
        for r in records:
            target = args.out / r["rel_path"]
            if not target.is_file():
                bad.append((r["slug"], "缺文件"))
            elif target.stat().st_size != r["bytes"]:
                bad.append((r["slug"], f"大小 {target.stat().st_size} != {r['bytes']}"))
            elif sha256_of(target) != r["sha256"]:
                bad.append((r["slug"], "sha256 不符"))
        print(f"[check] {len(records)} 条，问题 {len(bad)} 条")
        for slug, why in bad[:10]:
            print(f"   {slug}: {why}")
        return 1 if bad else 0

    files_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for r in records:
        target = files_dir / f"{r['slug']}.pdf"
        if target.is_file() and target.stat().st_size == r["bytes"] and sha256_of(target) == r["sha256"]:
            continue
        shutil.copyfile(args.src / r["_src"], target)
        got = sha256_of(target)
        assert got == r["sha256"], f"{r['slug']}: 复制后 sha256 {got} != {r['sha256']}"
        copied += 1

    index = {
        "generated_from": "zhenti.burningvocabulary.cn（pdf_index.json）",
        "count": len(records),
        "total_bytes": sum(r["bytes"] for r in records),
        "papers": [{k: v for k, v in r.items() if k != "_src"} for r in records],
    }
    (args.out / "index.json").write_bytes(
        json.dumps(index, ensure_ascii=False, indent=1).replace("\n", "\r\n").encode("utf-8")
    )
    print(
        f"[ok] {args.out}/index.json: {index['count']} 份 / {index['total_bytes'] / 1e6:.1f} MB（本次复制 {copied} 份）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

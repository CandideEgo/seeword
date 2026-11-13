"""Fail when the SQLAlchemy models grow new drift from the Alembic schema.

``alembic check`` against the developer database reports a long-standing
backlog (retired tables, legacy indexes, comments, a few missing constraints).
That backlog is listed below with a reason per entry: the point of this gate is
that **new** drift cannot sneak in silently, and the known debt stays visible
until a deliberate, data-safe migration retires it.

Usage (requires an already-migrated database):
    python scripts/check_schema_drift.py          # gate: exit 1 on new drift
    python scripts/check_schema_drift.py --list   # print every current diff

CI runs this in the e2e job right after ``alembic upgrade head``. Local:

    DATABASE_URL=postgresql+asyncpg://... python scripts/check_schema_drift.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# scripts/ is not on sys.path when invoked as `python scripts/...`; add the
# backend root so `app.*` imports resolve the same way they do under pytest.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.database import Base

# Import for the side effect, not for the name: registering every model on
# ``Base.metadata`` is what makes ``compare_metadata`` able to see the tables.
# Without it the comparison runs against empty metadata and reports every
# existing table as drift (or, depending on the version, nothing at all).
from app import models  # noqa: F401  isort: skip

# Known debt: diff key -> why it is allowed for now. Every entry should either
# disappear when its migration lands, or stay until a product decision is made.
# Empty since migration ``c3d4e5f6a7b8`` (2026-10 cleanup) dropped the retired
# speaking/quiz/practice tables this list used to excuse. Keep it empty: new
# drift must be fixed, not allowlisted.
KNOWN_DRIFT: dict[str, str] = {}


def _table_name(obj) -> str:
    return getattr(getattr(obj, "table", None), "name", "?") or "?"


def _diff_key(diff) -> str:
    if isinstance(diff, list):
        # modify_* comes as a one-element list of tuples.
        item = diff[0]
        kind, _schema, table, column, _kwargs, old, new = item
        if kind == "modify_nullable":
            return f"{kind}:{table}.{column}:{old}->{new}"
        return f"{kind}:{table}.{column}"
    kind = diff[0]
    if kind in ("add_table", "remove_table"):
        return f"{kind}:{diff[1].name}"
    if kind in ("add_index", "remove_index"):
        index = diff[1]
        return f"{kind}:{_table_name(index)}:{index.name}"
    if kind in ("add_constraint", "remove_constraint"):
        constraint = diff[1]
        name = constraint.name or ",".join(c.name for c in constraint.columns)
        return f"{kind}:{_table_name(constraint)}:{name}"
    if kind in ("add_fk", "remove_fk"):
        fk = diff[1]
        cols = ",".join(c.name for c in fk.columns)
        return f"{kind}:{_table_name(fk)}:{cols}"
    return f"{kind}:{diff[1]!r}"


async def _collect_diffs(database_url: str) -> list[str]:
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as conn:
            has_version = await conn.scalar(text("SELECT to_regclass('alembic_version')"))
            if has_version is None:
                raise SystemExit("database has no alembic_version — run `alembic upgrade head` first")
            diffs = await conn.run_sync(
                lambda sync_conn: compare_metadata(MigrationContext.configure(sync_conn), Base.metadata)
            )
    finally:
        await engine.dispose()
    return [_diff_key(d) for d in diffs]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="print current diff keys")
    args = parser.parse_args()

    settings = get_settings()
    keys = await _collect_diffs(settings.database_url)

    if args.list:
        for key in sorted(keys):
            print(key, "  #", KNOWN_DRIFT.get(key, "*** NOT ALLOWLISTED ***"))
        return 0

    unexpected = sorted(set(keys) - set(KNOWN_DRIFT))
    if unexpected:
        print("New model/migration drift detected:")
        for key in unexpected:
            print(f"  - {key}")
        print(
            "\nFix the model/migration mismatch, or add a reviewed entry to KNOWN_DRIFT in scripts/check_schema_drift.py."
        )
        return 1

    known_seen = sorted(set(keys) & set(KNOWN_DRIFT))
    print(f"Schema drift gate OK: {len(known_seen)} known entries, 0 new.")
    stale = sorted(set(KNOWN_DRIFT) - set(keys))
    if stale:
        print(f"Note: {len(stale)} allowlist entries no longer reproduce (cleanup candidate):")
        for key in stale:
            print(f"  - {key}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

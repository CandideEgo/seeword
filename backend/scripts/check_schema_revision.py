"""Read-only self-host release gate: actual database heads must equal image heads.

Run from backend with an explicitly configured DATABASE_URL. Does not migrate.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import create_async_engine


async def check_revision(database_url: str) -> tuple[set[str], set[str]]:
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "migrations"))
    expected = set(ScriptDirectory.from_config(config).get_heads())
    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            actual = await connection.run_sync(lambda c: set(MigrationContext.configure(c).get_current_heads()))
    finally:
        await engine.dispose()
    return actual, expected


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        print("DATABASE_URL must be explicitly set; refusing a development fallback")
        return 1
    try:
        actual, expected = asyncio.run(check_revision(database_url))
    except Exception as exc:
        # Driver errors may contain connection credentials; print the class only.
        print(f"Cannot verify schema revision ({type(exc).__name__})")
        return 1
    print(f"Database revisions: {', '.join(sorted(actual)) or '(none)'}")
    print(f"Image heads: {', '.join(sorted(expected)) or '(none)'}")
    if not expected or actual != expected:
        print("Schema revision mismatch; do not start API, worker or beat")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

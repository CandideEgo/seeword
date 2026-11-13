import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.database import Base

# Load every model so Base.metadata is complete before Alembic reads it. The
# per-model imports that used to sit here were a hand-kept subset of
# app.models.__init__ (and had drifted from it); importing the package once is
# both complete and honest — the name marks the import as intentional, which
# ruff's F401 check requires.
import app.models  # noqa: F401  (registers every table on Base.metadata)

config = context.config

# Resolve DATABASE_URL from environment — always overrides alembic.ini placeholder.
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # Fall back to app config if DATABASE_URL env var is not set directly
    try:
        from app.core.config import get_settings

        database_url = get_settings().database_url
    except Exception:
        pass
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

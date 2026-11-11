"""Presence checks for the V2 tables, so default-off deployments stay inert.

The V2 switches gate *capabilities*, not code paths. Before this module the
beat sweep, the data export and the account purge touched ``teaching_*`` /
``agent_*`` tables unconditionally, so a deployment whose migration failed
(the container keeps serving by design, see ``entrypoint.sh``) broke account
deletion and export -- silently, because the features that would have exposed
the drift were switched off.

Alembic commits one revision at a time, so a failed chain leaves a *prefix* of
the V2 tables behind. Callers therefore ask about the exact tables they are
about to touch, never a single sentinel.

P02.3 added *columns* to tables that already existed (``agent_runs``,
``teaching_messages``, ``agent_run_events``). A database stopped at the
previous head has every one of those tables but none of the columns, so a
table-presence check no longer proves the ORM can query them: the beat sweep
(every 10 s) and the account purge would raise ``ProgrammingError`` and keep
retrying. Callers that only need the pre-P02.3 shape use
``conversation_columns_ready`` to decide.
"""

from collections.abc import Iterable

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession


async def existing_tables(db: AsyncSession) -> frozenset[str]:
    connection = await db.connection()
    names = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    return frozenset(names)


async def existing_columns(db: AsyncSession, table: str) -> frozenset[str]:
    """Column names of ``table`` (empty if it does not exist)."""
    connection = await db.connection()
    names = await connection.run_sync(lambda sync: [c["name"] for c in inspect(sync).get_columns(table)])
    return frozenset(names)


async def has_tables(db: AsyncSession, names: Iterable[str]) -> bool:
    required = frozenset(names)
    return required <= await existing_tables(db)


async def missing_tables(db: AsyncSession, names: Iterable[str]) -> list[str]:
    """The subset of ``names`` this database does not have yet, in given order."""
    present = await existing_tables(db)
    return [name for name in names if name not in present]


# Every table owned by the V2 domains (teaching, runtime/connections,
# publication, question exposure). ``tests/test_v2_schema_gating.py`` keeps
# this in sync with the ORM so a new V2 model cannot be forgotten here.
V2_TABLES = frozenset(
    {
        "exam_analysis_revisions",
        "exam_evidence",
        "teaching_sessions",
        "teaching_items",
        "teaching_attempts",
        "user_question_disclosures",
        "teaching_operations",
        "teaching_feedbacks",
        "learning_event_outbox",
        "teaching_access_grants",
        "external_connections",
        "external_credentials",
        "agent_runs",
        "agent_steps",
        "agent_run_events",
        "teaching_messages",
        "teaching_message_blocks",
        "tutor_conversations",
        "tutor_conversation_tasks",
        "gateway_lifecycle_intents",
        "teaching_content_drafts",
        "content_publication_operations",
        "user_question_exposures",
        "user_exposure_mapping_states",
    }
)

# Tables the teaching sweep and its outbox delivery touch.
SWEEP_TABLES = (
    "agent_runs",
    "agent_run_events",
    "agent_steps",
    "teaching_feedbacks",
    "learning_event_outbox",
)

# Tables a conversation turn touches; the standalone chat API and the worker
# both gate on them so a partially migrated deployment fails closed with 503.
CONVERSATION_TABLES = (
    "tutor_conversations",
    "tutor_conversation_tasks",
    "teaching_messages",
    "teaching_message_blocks",
    "agent_runs",
    "agent_run_events",
    "agent_steps",
)

# Tables the teaching part of a user export reads. A deployment missing one
# of them predates the P02.3 conversation store; the ORM cannot read
# ``teaching_messages`` there anyway (its ``conversation_id`` column arrives in
# the same revision), so the whole teaching section is disclosed as empty
# rather than the export failing. HEAD and migrations ship together.
EXPORT_TABLES = (
    "teaching_sessions",
    "teaching_messages",
    "tutor_conversations",
    "tutor_conversation_tasks",
    "teaching_message_blocks",
    "agent_runs",
    "external_connections",
    "external_credentials",
    "teaching_operations",
    "teaching_feedbacks",
    "teaching_attempts",
    "user_question_disclosures",
)

# Tables the account purge explicitly clears (FK cascades cover the rest).
DELETE_TABLES = (
    "teaching_message_blocks",
    "teaching_messages",
    "tutor_conversation_tasks",
    "tutor_conversations",
    "agent_run_events",
    "agent_steps",
    "external_credentials",
    "learning_event_outbox",
    "teaching_attempts",
    "teaching_items",
    "external_connections",
    "teaching_sessions",
    "agent_runs",
    "teaching_access_grants",
    "teaching_feedbacks",
    "teaching_operations",
    "user_question_disclosures",
)


async def schema_ready(db: AsyncSession) -> bool:
    """True only when the whole V2 chain landed."""
    return await has_tables(db, V2_TABLES)


async def require_teaching_schema(db: AsyncSession) -> None:
    """503 (not 500) for teaching reads on a database without the V2 tables."""
    if not await schema_ready(db):
        from app.core.errors import AppError

        raise AppError(503, "SERVICE_UNAVAILABLE", "教学功能暂未开放")


# Columns P02.3 added to pre-existing tables. A deployment at the previous
# head has the tables but not these columns.
CONVERSATION_COLUMNS = (
    ("agent_runs", "conversation_id"),
    ("teaching_messages", "conversation_id"),
)


async def conversation_columns_ready(db: AsyncSession) -> bool:
    """True only when the ORM can select the conversation-era columns."""
    present = await existing_tables(db)
    if "agent_runs" not in present or "teaching_messages" not in present:
        return False
    for table, column in CONVERSATION_COLUMNS:
        if column not in await existing_columns(db, table):
            return False
    return True


async def require_conversation_schema(db: AsyncSession) -> None:
    """503 for the standalone chat API on a deployment without its tables."""
    if not await has_tables(db, CONVERSATION_TABLES):
        from app.core.errors import AppError

        raise AppError(503, "SERVICE_UNAVAILABLE", "教学功能暂未开放")

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
"""

from collections.abc import Iterable

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession


async def existing_tables(db: AsyncSession) -> frozenset[str]:
    connection = await db.connection()
    names = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    return frozenset(names)


async def has_tables(db: AsyncSession, names: Iterable[str]) -> bool:
    required = frozenset(names)
    return required <= await existing_tables(db)


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

# Tables the teaching part of a user export reads.
EXPORT_TABLES = (
    "teaching_sessions",
    "teaching_messages",
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

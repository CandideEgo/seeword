"""Dedicated teaching consumer. The cloud/default worker only performs sweeps."""

from app.core.database import get_async_session_maker
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.teaching_tasks.execute_teaching_run")
def execute_teaching_run(run_id: str):
    from app.services.teaching_runs import execute

    return run_async(execute(run_id))


async def _sweep():
    from app.services.teaching.events import deliver_pending_events
    from app.services.teaching_runs import sweep
    from app.services.v2_schema import SWEEP_TABLES, has_tables

    maker = get_async_session_maker()
    async with maker() as db:
        # The switch does not gate this task: an already-queued run must still
        # be swept after the feature is turned off. The *schema* does. Beat
        # schedules this every 10 s, so on a deployment whose V2 migration
        # never ran it would otherwise fail ~8.6k times a day and leave the
        # account purge's related cleanup in an unknown state.
        if not await has_tables(db, SWEEP_TABLES):
            return {"queued": 0, "skipped": "v2_schema_absent"}
        ids = await sweep(db)
    for run_id in ids:
        try:
            celery_app.send_task("app.tasks.teaching_tasks.execute_teaching_run", args=[run_id], queue="teaching")
        except Exception:
            from app.core.logging import get_logger

            get_logger(__name__).warning("teaching_dispatch_retry_deferred", run_id=run_id)
    async with maker() as db:
        await deliver_pending_events(db)
        await db.commit()
    return {"queued": len(ids)}


@celery_app.task(name="app.tasks.teaching_tasks.sweep_teaching_runs")
def sweep_teaching_runs():
    return run_async(_sweep())

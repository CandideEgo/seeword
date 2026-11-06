"""Assemble one task under a stable session version and current disclosure rules.

No commit, mutation, model call or second set of teaching rules lives here.
Adapters derive the principal; consumers cannot select a more privileged audience.
"""

from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.question_exposure import UserExposureMappingState, UserQuestionExposure
from app.models.teaching import ExamAnalysisRevision, TeachingItem, TeachingSession, UserQuestionDisclosure
from app.schemas.learning_context import LearningContext
from app.services.teaching import service as core
from app.services.teaching.principal import Principal, require_scope
from app.services.v2_access import require_access


def resume_url(session_id: str, item_id: str) -> str:
    return "/practice/exams/teaching?" + urlencode(
        {"mode": "teach", "teaching_session_id": session_id, "item": item_id}
    )


async def _allowed_actions(db: AsyncSession, principal: Principal, *, active: bool, restricted: bool) -> list[str]:
    if not active or restricted or principal.actor not in {"user_ui", "external_agent"}:
        return []
    if principal.actor == "external_agent":
        try:
            await require_access(db, principal.user_id, "mcp_write_enabled")
        except AppError:
            return []
    actions = []
    for action, operation in (
        ("save_draft", "draft"),
        ("submit_attempt", "attempt"),
        ("request_hint", "hint"),
        ("reveal_answer", "reveal"),
        ("record_feedback", "feedback"),
        ("complete_session", "complete"),
    ):
        try:
            await core.check_write_access(db, principal, operation)
            if operation == "reveal":
                require_scope(principal, "teaching:analysis:read", write=True)
        except AppError:
            continue
        actions.append(action)
    return actions


async def get_learning_context(db: AsyncSession, principal: Principal, session_id: str) -> LearningContext:
    from app.services.v2_schema import require_teaching_schema

    require_scope(principal, "teaching:read")
    await require_teaching_schema(db)
    # A read lock prevents a writer committing between the state-version read
    # and its item/attempt projection. It ends with the adapter's transaction;
    # never keep this transaction open across a model/provider request.
    session = await db.scalar(
        select(TeachingSession)
        .where(TeachingSession.id == session_id, TeachingSession.user_id == principal.user_id)
        .with_for_update(read=True)
        .execution_options(populate_existing=True)
    )
    if session is None:
        raise AppError(404, "NOT_FOUND", "教学会话不存在")
    item = await db.get(TeachingItem, session.current_item_id, populate_existing=True)
    if item is None or item.session_id != session.id:
        raise AppError(409, "TEACHING_STATE_CONFLICT", "当前教学题目不可用")
    revision = await db.get(
        ExamAnalysisRevision, item.content_revision_id, with_for_update={"read": True}, populate_existing=True
    )
    if revision is None:
        raise AppError(409, "CONTENT_RESTRICTED", "教学内容不可用")
    state = await core.project_session(db, principal, session, attempt_limit=5)
    public_item = next(row for row in state["items"] if row["id"] == item.id)
    cards = [card for card in state["cards"] if card["item_id"] == item.id]
    restricted = not any(card["kind"] == "question" for card in cards)
    audience = core.projection_target(principal)
    may_read_answers = core.answer_history_visible(principal, restricted=restricted)
    attempts = [row for row in state["attempts"] if row["item_id"] == item.id]
    exposure = await db.get(UserQuestionExposure, (principal.user_id, item.question_key), populate_existing=True)
    mapping = await db.get(UserExposureMappingState, principal.user_id, populate_existing=True)
    disclosure = await db.get(UserQuestionDisclosure, (principal.user_id, revision.id), populate_existing=True)
    actions = await _allowed_actions(db, principal, active=session.status == "active", restricted=restricted)
    return LearningContext.model_validate(
        {
            "schema_version": 1,
            "audience": audience,
            "task": {
                "session_id": session.id,
                "item_id": item.id,
                "status": session.status,
                "state": item.state,
                "state_version": session.revision,
                "teaching_policy_version": session.policy_version,
            },
            "material": {
                "question_key": item.question_key,
                "content_revision_id": revision.id,
                "source_fingerprint": revision.source_fingerprint,
                "grading_version": revision.grading_version,
                "normalization_version": revision.normalization_version,
                "restricted": restricted,
            },
            "progress": {
                "draft_answer": public_item["draft_answer"],
                "draft_revision": item.draft_revision,
                "answers_visible": may_read_answers,
                "attempt_count": item.next_attempt_no - 1,
                "recent_attempts": attempts[-5:],
                "attempts_truncated": may_read_answers and item.next_attempt_no - 1 > len(attempts),
                "help": {
                    "hint_level": item.hint_level,
                    "max_hint_level": exposure.max_hint_level if exposure else 0,
                    "feedback_count": exposure.feedback_count if exposure else 0,
                    "answer_available": bool(exposure and exposure.first_answer_available_at),
                    "analysis_revealed": bool(disclosure and disclosure.analysis_revealed_at),
                    "history_status": "complete" if mapping and mapping.status == "complete" else "unknown",
                },
            },
            "cards": cards,
            "allowed_actions": actions,
            "resume_url": resume_url(session.id, item.id),
        }
    )

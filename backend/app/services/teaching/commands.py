"""One command entry for every explicit teaching write.

Buttons on the teaching page and buttons inside a quiz card must not grow two
write paths. Each action here resolves to the *same* domain service the legacy
per-action endpoints call, carrying the caller's ``operation_id`` unchanged so
the existing ``TeachingOperation`` receipt keeps providing idempotency: a
duplicated click or a network retry returns the first attempt, never a second.

The command layer adds exactly two things of its own:

* it refuses every actor except ``user_ui`` — a model or an external agent may
  propose an action, but the write stays in the user's hands; and
* it keeps the request shape flat, so one wire schema covers all six actions.

Natural-language turns ("I pick B") are *not* parsed here. That needs model
intent resolution and belongs to the P02.5 slice; until then this layer is only
reached by explicit user actions.
"""

from typing import TYPE_CHECKING

from app.core.errors import AppError
from app.schemas.teaching import (
    CompleteSession,
    DraftAnswer,
    Feedback,
    ItemAction,
    SessionActionRequest,
    SubmitAttempt,
)
from app.services.teaching import service

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.services.teaching.principal import Principal


def _require_ui(principal: "Principal") -> None:
    # ``require_scope(..., write=True)`` already blocks the model and system
    # actors; this is the stricter rule for this entry: even a write-scoped
    # external connection must not drive a quiz card.
    if principal.actor != "user_ui":
        raise AppError(403, "INSUFFICIENT_SCOPE", "该动作只能由用户在网页上执行")


def _item(body: SessionActionRequest) -> dict:
    if not body.item_id:
        raise AppError(422, "VALIDATION_ERROR", "item_id 必填")
    return {
        "operation_id": body.operation_id,
        "expected_revision": body.expected_revision,
        "item_id": body.item_id,
    }


async def execute(db: "AsyncSession", principal: "Principal", session_id: str, body: SessionActionRequest) -> dict:
    """Dispatch one session action to its domain service and project the result."""
    _require_ui(principal)
    action = body.action

    if action == "draft":
        return await service.save_draft(db, principal, session_id, DraftAnswer(**_item(body), answer=body.answer))
    if action == "attempts":
        if not body.answer:
            raise AppError(422, "VALIDATION_ERROR", "answer 必填")
        return await service.submit_attempt(db, principal, session_id, SubmitAttempt(**_item(body), answer=body.answer))
    if action == "hints":
        return await service.request_hint(db, principal, session_id, ItemAction(**_item(body)))
    if action == "reveal":
        return await service.reveal_answer(db, principal, session_id, ItemAction(**_item(body)))
    if action == "feedback":
        if not body.content:
            raise AppError(422, "VALIDATION_ERROR", "content 必填")
        return await service.record_feedback(db, principal, session_id, Feedback(**_item(body), content=body.content))
    if action == "complete":
        return await service.complete_session(
            db,
            principal,
            session_id,
            CompleteSession(operation_id=body.operation_id, expected_revision=body.expected_revision),
        )
    raise AppError(422, "VALIDATION_ERROR", "未知的教学动作")

"""P02.4: frozen four-question quizzes and the single command entry.

Everything here runs on deterministic code with synthetic original fixtures:
no model call is involved, and none of the assertions would pass if the quiz
score were stored in a second ledger — every number is projected from the
item's own attempts and disclosure rows.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.errors import AppError
from app.models.exam_test import ExamAnswer, ExamSession
from app.models.question_exposure import UserQuestionExposure
from app.models.teaching import TeachingAttempt, TeachingFeedback, TeachingOperation
from app.models.user import User
from app.schemas.teaching import SessionActionRequest, SessionResponse
from app.services import v2_access
from app.services.teaching import commands, service
from app.services.teaching.principal import Principal
from tests.teaching_fixtures import QUIZ_QUESTIONS, seed_quiz_content


def enable(monkeypatch, user_id):
    settings = SimpleNamespace(teaching_enabled=True, teaching_allowed_user_ids=user_id)
    monkeypatch.setattr(v2_access, "get_settings", lambda: settings)
    return settings


def act(state, operation_id, action, item_id=None, **extra):
    return SessionActionRequest(
        operation_id=operation_id,
        expected_revision=state["revision"],
        action=action,
        item_id=item_id or state["current_item_id"],
        **extra,
    )


async def _quiz(db, monkeypatch):
    user, paper, revisions = await seed_quiz_content(db)
    enable(monkeypatch, user.id)
    return user, paper, revisions, Principal(user.id)


def _progress(state):
    card = next(card for card in state["cards"] if card["kind"] == "progress")
    return card["payload"]


async def test_quiz_freezes_four_questions_without_leaking_answers(db_session, monkeypatch):
    _user, paper, revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()

    assert len(state["items"]) == 4
    assert [item["question_key"] for item in state["items"]] == [revision.question_key for revision in revisions]
    assert _progress(state) == {"answered": 0, "correct": 0, "total": 4, "item_ids": [i["id"] for i in state["items"]]}
    SessionResponse.model_validate(state)

    # Before any answer: no card, field or item may carry the standard answer.
    for name in ("correct_answer", "analysis_payload", "reviewed_hints", "option_analyses"):
        assert name not in str(state), name
    assert {card["kind"] for card in state["cards"]} == {"question", "progress"}
    assert all(item["answered"] is False and item["correct"] is None for item in state["items"])


async def test_quiz_requires_exactly_four_usable_questions(db_session, monkeypatch):
    _user, _paper, revisions, principal = await _quiz(db_session, monkeypatch)
    with pytest.raises(AppError) as short:
        await service.create_quiz(
            db_session,
            principal,
            {"operation_id": "three", "revision_ids": [r.id for r in revisions[:3]]},
        )
    assert short.value.status_code == 422

    with pytest.raises(AppError) as dup:
        await service.create_quiz(
            db_session,
            principal,
            {"operation_id": "dup", "revision_ids": [revisions[0].id] * 4},
        )
    assert dup.value.status_code == 422


async def test_withdrawn_material_never_enters_a_quiz(db_session, monkeypatch):
    _user, paper, revisions, principal = await _quiz(db_session, monkeypatch)
    revisions[2].status = "withdrawn"
    await db_session.commit()

    # Only four verified questions exist, so withdrawing one leaves three: a
    # quiz is four questions or it is nothing, never a short one.
    with pytest.raises(AppError) as short:
        await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    assert short.value.status_code == 422

    # Asking for the withdrawn one explicitly is refused, not substituted.
    with pytest.raises(AppError) as explicit:
        await service.create_quiz(
            db_session,
            principal,
            {"operation_id": "explicit", "revision_ids": [r.id for r in revisions]},
        )
    assert explicit.value.status_code == 409


async def test_repeated_action_counts_once_and_projects_progress(db_session, monkeypatch):
    user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    first_item, second_item = state["items"][0], state["items"][1]

    body = act(state, "answer-1", "attempts", item_id=first_item["id"], answer="B")
    answered = await commands.execute(db_session, principal, state["id"], body)
    await db_session.commit()
    assert _progress(answered)["answered"] == 1
    assert _progress(answered)["correct"] == 1
    assert answered["items"][0]["correct"] is True

    # Same operation id -> replay, no second attempt, no double-counted feedback.
    replay = await commands.execute(db_session, principal, state["id"], body)
    await db_session.commit()
    assert replay["replayed"] is True
    assert _progress(replay)["answered"] == 1
    attempts = await db_session.scalar(
        select(func.count()).select_from(TeachingAttempt).where(TeachingAttempt.item_id == first_item["id"])
    )
    assert attempts == 1
    exposure = await db_session.get(UserQuestionExposure, (user.id, first_item["question_key"]))
    assert exposure.feedback_count == 1

    # A wrong answer on another question moves only that question's progress.
    wrong = await commands.execute(
        db_session, principal, state["id"], act(replay, "answer-2", "attempts", item_id=second_item["id"], answer="A")
    )
    await db_session.commit()
    progress = _progress(wrong)
    assert (progress["answered"], progress["correct"], progress["total"]) == (2, 1, 4)
    assert wrong["items"][0]["correct"] is True and wrong["items"][1]["correct"] is False
    assert wrong["items"][2]["answered"] is False


async def test_stale_revision_is_rejected_not_silently_applied(db_session, monkeypatch):
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    stale = SessionActionRequest(
        operation_id="stale",
        expected_revision=state["revision"] + 5,
        action="attempts",
        item_id=state["items"][0]["id"],
        answer="B",
    )
    with pytest.raises(AppError) as exc:
        await commands.execute(db_session, principal, state["id"], stale)
    assert exc.value.code == "TEACHING_REVISION_CONFLICT"


async def test_revealing_one_question_does_not_disclose_another(db_session, monkeypatch):
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    first, second = state["items"][0], state["items"][1]

    revealed = await commands.execute(
        db_session, principal, state["id"], act(state, "reveal-1", "reveal", item_id=first["id"])
    )
    await db_session.commit()
    analysis = [card for card in revealed["cards"] if card["kind"] == "analysis"]
    assert analysis and analysis[0]["item_id"] == first["id"]
    assert all(card["item_id"] != second["id"] for card in analysis)

    second_view = await service.get_session(db_session, principal, state["id"])
    assert second_view["items"][1]["correct"] is None
    assert not any(card["kind"] == "analysis" and card["item_id"] == second["id"] for card in second_view["cards"])


async def test_quiz_answers_never_touch_the_formal_exam_tables(db_session, monkeypatch):
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    for index, item in enumerate(state["items"]):
        state = await commands.execute(
            db_session,
            principal,
            state["id"],
            act(state, f"answer-{index}", "attempts", item_id=item["id"], answer="B"),
        )
        await db_session.commit()
    assert await db_session.scalar(select(func.count()).select_from(ExamAnswer)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ExamSession)) == 0


@pytest.mark.parametrize("actor", ["internal_agent", "external_agent", "system"])
async def test_only_the_user_may_drive_a_quiz_action(db_session, monkeypatch, actor):
    user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    body = act(state, f"answer-{actor}", "attempts", answer="B")
    other = Principal(user.id, actor=actor)
    with pytest.raises(AppError) as exc:
        await commands.execute(db_session, other, state["id"], body)
    assert exc.value.status_code == 403
    assert await db_session.scalar(select(func.count()).select_from(TeachingAttempt)) == 0


async def test_progress_hidden_where_answer_history_is_hidden(db_session, monkeypatch):
    """A read-only scope must not turn progress into an answer oracle."""
    user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    state = await commands.execute(db_session, principal, state["id"], act(state, "answer", "attempts", answer="B"))
    await db_session.commit()

    # A read-only external scope may read the session but not the answer history,
    # so progress must be withheld rather than becoming an answer oracle.
    read_only = Principal(
        user.id, actor="external_agent", connection_id="conn-1", granted_scopes=frozenset({"teaching:read"})
    )
    hidden = await service.get_session(db_session, read_only, state["id"])
    assert all(item["answered"] is False and item["correct"] is None for item in hidden["items"])
    assert _progress(hidden) == {
        "answered": 0,
        "correct": 0,
        "total": 4,
        "item_ids": [i["id"] for i in hidden["items"]],
    }


async def test_unknown_action_and_missing_fields_are_rejected(db_session, monkeypatch):
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()

    with pytest.raises(AppError) as no_item:
        await commands.execute(
            db_session,
            principal,
            state["id"],
            SessionActionRequest(operation_id="x", expected_revision=1, action="hints"),
        )
    assert no_item.value.status_code == 422

    with pytest.raises(AppError) as no_answer:
        await commands.execute(db_session, principal, state["id"], act(state, "x", "attempts"))
    assert no_answer.value.status_code == 422

    with pytest.raises(AppError) as no_content:
        await commands.execute(db_session, principal, state["id"], act(state, "x", "feedback"))
    assert no_content.value.status_code == 422


async def test_http_quiz_and_action_entry_replay(client, auth_headers, db_session, monkeypatch):
    user = await db_session.scalar(select(User).where(User.phone == "13800138000"))
    user, paper, _revisions = await seed_quiz_content(db_session, existing_user=user)
    enable(monkeypatch, user.id)

    body = {"operation_id": "http-quiz", "paper_id": paper.id}
    created = await client.post("/api/v1/teaching/quizzes", json=body, headers=auth_headers)
    assert created.status_code == 201, created.text
    state = created.json()
    assert len(state["items"]) == 4
    replay = await client.post("/api/v1/teaching/quizzes", json=body, headers=auth_headers)
    assert replay.status_code == 200 and replay.json()["id"] == state["id"]

    payload = {
        "operation_id": "http-action",
        "expected_revision": state["revision"],
        "action": "attempts",
        "item_id": state["items"][0]["id"],
        "answer": "B",
    }
    first = await client.post(f"/api/v1/teaching/sessions/{state['id']}/actions", json=payload, headers=auth_headers)
    assert first.status_code == 200 and first.json()["items"][0]["answered"] is True
    again = await client.post(f"/api/v1/teaching/sessions/{state['id']}/actions", json=payload, headers=auth_headers)
    assert again.status_code == 200 and again.json()["replayed"] is True

    unknown = await client.post(
        f"/api/v1/teaching/sessions/{state['id']}/actions",
        json={**payload, "operation_id": "http-bad", "action": "launch"},
        headers=auth_headers,
    )
    assert unknown.status_code == 422


async def test_action_operation_receipt_is_scoped_per_user(db_session, monkeypatch):
    """The receipt lives in TeachingOperation; a second user cannot replay it."""
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    await commands.execute(db_session, principal, state["id"], act(state, "shared-op", "attempts", answer="B"))
    await db_session.commit()

    other = User(name="Other learner")
    db_session.add(other)
    await db_session.commit()
    enable(monkeypatch, other.id)
    with pytest.raises(AppError) as exc:
        await commands.execute(
            db_session, Principal(other.id), state["id"], act(state, "shared-op", "attempts", answer="B")
        )
    assert exc.value.status_code == 404
    # One receipt for the quiz start, one for the answer — the other user added none.
    assert await db_session.scalar(select(func.count()).select_from(TeachingOperation)) == 2


async def test_quiz_action_keeps_every_domain_fact_consistent(db_session, monkeypatch):
    """No second ledger: attempts, exposures and operations all agree."""
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    for index, item in enumerate(state["items"][:2]):
        state = await commands.execute(
            db_session, principal, state["id"], act(state, f"a{index}", "attempts", item_id=item["id"], answer="B")
        )
        await db_session.commit()

    attempts = await db_session.scalar(select(func.count()).select_from(TeachingAttempt))
    operations = await db_session.scalar(
        select(func.count()).select_from(TeachingOperation).where(TeachingOperation.operation_type == "attempt")
    )
    assert attempts == 2 and operations == 2
    assert await db_session.scalar(select(func.count()).select_from(TeachingFeedback)) == 0
    assert _progress(state)["answered"] == 2


async def test_limited_attempt_read_keeps_progress_consistent(db_session, monkeypatch):
    """A bounded attempt read must not break projection (regression).

    The learning context asks for ``attempt_limit=5``; an item graded under a
    scope whose attempt rows are not readable still has ``next_attempt_no > 1``,
    so the verdict lookup must tolerate an empty row set instead of indexing it.
    """
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    state = await commands.execute(db_session, principal, state["id"], act(state, "answer", "attempts", answer="B"))
    await db_session.commit()

    bounded = await service.project_session(
        db_session, principal, await service.owned_session(db_session, principal, state["id"]), attempt_limit=5
    )
    assert bounded["items"][0]["answered"] is True
    assert bounded["items"][0]["correct"] is True


async def test_quiz_question_text_comes_from_the_fixture(db_session, monkeypatch):
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()
    questions = [card["payload"]["question"] for card in state["cards"] if card["kind"] == "question"]
    assert questions == list(QUIZ_QUESTIONS)


async def test_revealing_and_hinting_every_question_still_finishes(db_session, monkeypatch):
    """Regression: the fixed 8-card cap made the normal quiz path unendable.

    Four questions x (question + hint + analysis + evidence) legitimately exceeds
    eight cards. With the old bound the second reveal and the fourth hint raised
    409, and ``complete`` re-raised it on every retry — the session could never
    leave ``active``.
    """
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()

    for index, item in enumerate(state["items"]):
        state = await commands.execute(
            db_session, principal, state["id"], act(state, f"hint-{index}", "hints", item_id=item["id"])
        )
        await db_session.commit()
        state = await commands.execute(
            db_session, principal, state["id"], act(state, f"reveal-{index}", "reveal", item_id=item["id"])
        )
        await db_session.commit()

    assert len(state["cards"]) > 8
    SessionResponse.model_validate(state)
    finished = await commands.execute(db_session, principal, state["id"], act(state, "finish", "complete"))
    await db_session.commit()
    assert finished["status"] == "completed"


async def test_abandon_is_its_own_command(db_session, monkeypatch):
    """The web button used to send ``{action:'complete', action:'abandon'}``.

    A flat body made those collide, so the request was rejected as an unknown
    action and "结束本次" was unreachable from the page.
    """
    _user, paper, _revisions, principal = await _quiz(db_session, monkeypatch)
    state = await service.create_quiz(db_session, principal, {"operation_id": "quiz", "paper_id": paper.id})
    await db_session.commit()

    abandoned = await commands.execute(db_session, principal, state["id"], act(state, "ab", "abandon"))
    await db_session.commit()
    assert abandoned["status"] == "abandoned"


async def test_paper_scope_takes_the_first_four_questions(db_session, monkeypatch):
    """A real CET-4 paper holds far more than four verified questions."""
    from app.models.exam_test import ExamQuestion
    from app.services.teaching.content import publish_revision
    from tests.teaching_fixtures import original_candidate

    _user, paper, revisions, principal = await _quiz(db_session, monkeypatch)

    async def accept(_receipt):
        return True

    for number in (50, 51):
        candidate = original_candidate(number=number, question=f"Extra question {number}?", set_no=3, year=2024)
        payload = candidate["question_payload"]
        extra = ExamQuestion(
            paper_id=paper.id,
            section="reading_C",
            number=payload["number"],
            question_type="reading",
            passage=payload["passage"],
            question=payload["question"],
            options=payload["options"],
            answer="B",
        )
        db_session.add(extra)
        await db_session.flush()
        candidate["question_id"] = extra.id
        await publish_revision(db_session, candidate, verify_receipt=accept)
    await db_session.commit()

    state = await service.create_quiz(db_session, principal, {"operation_id": "six", "paper_id": paper.id})
    await db_session.commit()
    assert len(state["items"]) == 4
    # Paper order (46, 47, 48, 49), never the string order of question_key.
    assert [item["question_key"].rsplit(":", 1)[-1] for item in state["items"]] == ["46", "47", "48", "49"]

    with pytest.raises(AppError) as missing:
        await service.create_quiz(
            db_session, principal, {"operation_id": "two", "revision_ids": [r.id for r in revisions[:2]]}
        )
    assert missing.value.status_code == 422

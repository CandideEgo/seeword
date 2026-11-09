"""Original synthetic teaching artifacts, never imported into dev/production."""

import copy
import hashlib

from app.models.exam_test import ExamPaper, ExamQuestion
from app.models.question_exposure import UserExposureMappingState
from app.models.user import User
from app.services.teaching.content import normalized_question, publish_revision, stable_hash


def original_candidate(
    *,
    number: int = 46,
    question: str = "What did the garden team find?",
    set_no: int = 1,
    year: int = 2025,
    month: int = 12,
) -> dict:
    passage = "The garden team tested blue pots. 🌱 The blue pots retained water longer than the red pots. The team measured both groups every morning."
    quote = "The blue pots retained water longer than the red pots."
    start = passage.index(quote)
    payload = {
        "level": "cet4",
        "year": year,
        "month": month,
        "set_no": set_no,
        "number": number,
        "question_type": "reading",
        "passage": passage,
        "question": question,
        "options": {
            "A": "Red pots were heavier.",
            "B": "Blue pots held moisture longer.",
            "C": "Both pots were equally dry.",
            "D": "Pots changed the morning temperature.",
        },
    }
    normalized = normalized_question(payload)
    sources = []
    for kind, group, answer in (
        ("paper", "original-paper", None),
        ("answer", "original-key-a", "B"),
        ("answer", "original-key-b", "B"),
    ):
        sources.append(
            {
                "kind": kind,
                "independent_group": group,
                "uri": f"urn:seeword:original:fixture:{group}",
                "artifact_sha256": hashlib.sha256(group.encode()).hexdigest(),
                "question_payload": copy.deepcopy(payload),
                "answer": answer,
                "snapshot_sha256": stable_hash({"question": normalized, "answer": answer}),
            }
        )
    candidate = {
        "question_payload": payload,
        "correct_answer": "B",
        "learning_objectives": ["Find an explicit comparison."],
        "option_analyses": {
            "A": "Weight was not compared.",
            "B": "The passage states that the blue pots retained water longer.",
            "C": "The passage reports a difference.",
            "D": "Temperature was not measured.",
        },
        "reviewed_hints": ["Find the sentence comparing the two groups.", "Focus on what the team measured."],
        "analysis_payload": {"summary": "The observed difference concerns water retention."},
        "rights_policy": {
            "site_display": True,
            "model_processing": True,
            "external_redistribution": True,
            "evidence_uri": "urn:seeword:original:fixture",
            "evidence_sha256": hashlib.sha256(passage.encode()).hexdigest(),
        },
        "evidence": [
            {
                "start": start,
                "end": start + len(quote),
                "quote": quote,
                "quote_hash": hashlib.sha256(quote.encode()).hexdigest(),
            }
        ],
        "verification_report": {
            "policy_version": "automatic-consensus-v1",
            "sources": sources,
            "blind_answers": [
                {
                    "model": "synthetic-test-only",
                    "model_family": f"fixture-family-{i}",
                    "provider_attempt_id": f"synthetic-receipt-{i}",
                    "input_sha256": stable_hash(normalized),
                    "option_order": order,
                    "selected_position": order.index("B"),
                }
                for i, order in enumerate((list("CADB"), list("BDAC")))
            ],
        },
    }
    teaching_hash = stable_hash(
        {
            "question": normalized,
            "correct_answer": candidate["correct_answer"],
            "option_analyses": candidate["option_analyses"],
            "hints": candidate["reviewed_hints"],
            "analysis": candidate["analysis_payload"],
            "evidence": candidate["evidence"],
        }
    )
    candidate["verification_report"]["teaching_checks"] = [
        {
            "model": "synthetic-test-only",
            "model_family": f"fixture-family-{i}",
            "provider_attempt_id": f"synthetic-teaching-receipt-{i}",
            "input_sha256": teaching_hash,
            "checks": {
                "evidence_entails_answer": True,
                "distractors_supported": True,
                "hints_non_revealing": True,
                "one_correct_option": True,
            },
        }
        for i in range(2)
    ]
    return candidate


async def seed_original_content(db, *, existing_user=None, complete_history=True):
    user = existing_user or User(name="Synthetic teaching user")
    if not existing_user:
        db.add(user)
    paper = ExamPaper(
        level="cet4",
        year=2025,
        month=12,
        set_no=1,
        title="Original synthetic fixture",
        source="Original synthetic test",
        total_questions=1,
    )
    db.add(paper)
    await db.flush()
    candidate = original_candidate()
    p = candidate["question_payload"]
    question = ExamQuestion(
        paper_id=paper.id,
        section="reading_C",
        number=p["number"],
        question_type="reading",
        passage=p["passage"],
        question=p["question"],
        options=p["options"],
        answer="B",
    )
    db.add(question)
    await db.flush()
    candidate["question_id"] = question.id

    async def synthetic_receipt_verifier(_receipt):
        # Only isolated tests supply this stub; product import has no fallback.
        return True

    revision = await publish_revision(db, candidate, verify_receipt=synthetic_receipt_verifier)
    db.add(UserExposureMappingState(user_id=user.id, status="complete" if complete_history else "unknown"))
    await db.commit()
    return user, revision, question, candidate


QUIZ_QUESTIONS = (
    "What did the garden team compare?",
    "Which pots held moisture longer?",
    "How often did the team measure?",
    "What is the passage mainly about?",
)


async def seed_quiz_content(db, *, existing_user=None):
    """Four verified, distinct questions on one paper — the P02.4 quiz shape.

    Synthetic original material, never real exam content: the receipt verifier
    is a stub, so these revisions only exercise the deterministic teaching code
    path. Publication of real material still requires real receipts.
    """
    user = existing_user or User(name="Synthetic quiz user")
    if not existing_user:
        db.add(user)
    paper = ExamPaper(
        level="cet4",
        year=2024,
        month=12,
        set_no=3,
        title="Original synthetic quiz fixture",
        source="Original synthetic test",
        total_questions=len(QUIZ_QUESTIONS),
    )
    db.add(paper)
    await db.flush()

    revisions = []
    for offset, question_text in enumerate(QUIZ_QUESTIONS):
        candidate = original_candidate(number=46 + offset, question=question_text, set_no=3, year=2024)
        payload = candidate["question_payload"]
        question = ExamQuestion(
            paper_id=paper.id,
            section="reading_C",
            number=payload["number"],
            question_type="reading",
            passage=payload["passage"],
            question=payload["question"],
            options=payload["options"],
            answer="B",
        )
        db.add(question)
        await db.flush()
        candidate["question_id"] = question.id

        async def synthetic_receipt_verifier(_receipt):
            return True

        revisions.append(await publish_revision(db, candidate, verify_receipt=synthetic_receipt_verifier))

    db.add(UserExposureMappingState(user_id=user.id, status="complete"))
    await db.commit()
    return user, paper, revisions

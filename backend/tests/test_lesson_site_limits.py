"""Online storage bounds reject at import; portable SLCS remains unchanged."""

import json

import pytest
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.lesson import Lesson, LessonOperation, LessonRevision
from app.models.user import User
from app.services import lesson_catalog, lessons
from app.services.teaching.principal import Principal
from slcs import FINGERPRINT_VERSION, fingerprint, load_pack, tokenize
from tests.open_learning_fixtures import synthetic_pack


def bounded_pack(kind: str, size: int) -> dict:
    pack = synthetic_pack()
    if kind == "segment":
        pack["segments"][0]["id"] = "s" * size
        pack["vocabulary"][0]["segment_id"] = "s" * size
    elif kind == "token":
        pack["segments"][0]["tokens"][2]["id"] = "w" * size
        pack["vocabulary"][0]["token_ids"][0] = "w" * size
    else:
        segment = pack["segments"][0]
        segment["text"] = " ".join(["word"] * size) + "."
        segment["translation"] = "合成的长词组。"
        segment["tokens"] = [
            {
                "id": f"w{index:03}",
                "start_char": start,
                "end_char": end,
                "timing": {"start_ms": index * 5, "end_ms": (index + 1) * 5},
            }
            for index, (start, end) in enumerate(tokenize(segment["text"]))
        ]
        pack["vocabulary"][0]["headword"] = "wide phrase"
        pack["vocabulary"][0]["token_ids"] = [token["id"] for token in segment["tokens"]]
    return pack


@pytest.mark.parametrize(
    "kind,size,path",
    [
        ("segment", 101, "/segments/0/id"),
        ("token", 101, "/segments/0/tokens/2/id"),
        ("span", 129, "/vocabulary/0/token_ids"),
    ],
)
async def test_site_refuses_unsupported_anchors_before_creating_candidate(db_session, kind, size, path):
    payload = json.dumps(bounded_pack(kind, size)).encode()
    assert load_pack(payload)  # This remains legal in the independent portable format.
    actor = User()
    db_session.add(actor)
    await db_session.flush()
    with pytest.raises(AppError) as error:
        await lessons.import_lesson(db_session, actor.id, "bounded-import", payload)
    assert error.value.status_code == 422
    assert error.value.detail[0]["path"] == path
    assert await db_session.scalar(select(func.count()).select_from(LessonRevision)) == 0
    assert await db_session.scalar(select(func.count()).select_from(LessonOperation)) == 0


@pytest.mark.parametrize("kind,size", [("segment", 100), ("token", 100), ("span", 128)])
async def test_accepted_online_boundaries_can_generate_fixed_references(db_session, monkeypatch, kind, size):
    monkeypatch.setattr(get_settings(), "slcs_lessons_enabled", True)
    payload = json.dumps(bounded_pack(kind, size)).encode()
    actor = User()
    db_session.add(actor)
    await db_session.flush()
    detail = await lessons.import_lesson(db_session, actor.id, "boundary-import", payload)
    revision = await db_session.get(LessonRevision, detail["revision_id"])
    # Isolated read-contract fixture, not publication/rights evidence.
    revision.status = "published"
    revision.review = {"uses": {"site_display": {"approved": True}}}
    lesson = await db_session.get(Lesson, revision.lesson_id)
    lesson.current_revision_id = revision.id
    await db_session.commit()
    query = "wide phrase" if kind == "span" else "public domain"
    result = await lesson_catalog.search_occurrences(db_session, Principal(actor.id), query)
    assert result["total"] == 1
    assert len(result["items"][0]["reference"]["token_ids"]) == (128 if kind == "span" else 2)


async def test_legacy_over_limit_pack_fails_explicitly_not_during_response_serialization(db_session, monkeypatch):
    monkeypatch.setattr(get_settings(), "slcs_lessons_enabled", True)
    pack = load_pack(json.dumps(bounded_pack("segment", 101)).encode())
    lesson = Lesson(id=pack.lesson_id)
    db_session.add(lesson)
    await db_session.flush()
    revision = LessonRevision(
        lesson_id=lesson.id,
        title=pack.title,
        fingerprint=fingerprint(pack),
        fingerprint_version=FINGERPRINT_VERSION,
        access_mode="external_link",
        pack=pack.model_dump(mode="json"),
        status="published",
        review={
            "uses": {
                use: {"approved": use == "site_display"}
                for use in ("site_display", "model_processing", "external_redistribution")
            }
        },
    )
    db_session.add(revision)
    await db_session.flush()
    lesson.current_revision_id = revision.id
    await db_session.commit()
    assert lessons.public_detail(revision)["pack"]["segments"][0]["id"] == "s" * 101
    with pytest.raises(AppError) as error:
        await lesson_catalog.search_occurrences(db_session, Principal("reader"), "public domain")
    assert error.value.status_code == 422 and error.value.detail[0]["path"] == "/segments/0/id"

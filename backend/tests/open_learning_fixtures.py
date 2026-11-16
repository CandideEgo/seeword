"""Original synthetic content for engineering tests, not a rights attestation."""

import json

from app.models.lesson import Lesson, LessonRevision
from app.services.lessons import material_for_revision
from slcs import FINGERPRINT_VERSION, fingerprint, load_pack, tokenize


def synthetic_pack(lesson_id: str = "synthetic-learning", title: str = "Synthetic learning") -> dict:
    sentences = [
        ("We study public domain examples.", "我们学习公有领域的示例。"),
        ("A bank can hold money.", "银行可以保管钱。"),
        ("The river bank is quiet.", "这处河岸很安静。"),
    ]
    segments = []
    for index, (text, translation) in enumerate(sentences):
        start = index * 1500
        spans = tokenize(text)
        segments.append(
            {
                "id": f"s{index + 1:02}",
                "start_ms": start,
                "end_ms": start + 1000,
                "text": text,
                "translation": translation,
                "tokens": [
                    {
                        "id": f"w{word + 1:02}",
                        "start_char": left,
                        "end_char": right,
                        "timing": {"start_ms": start + word * 100, "end_ms": start + (word + 1) * 100},
                    }
                    for word, (left, right) in enumerate(spans)
                ],
            }
        )
    rights = {
        "attribution": "SeeWord synthetic engineering fixture",
        "basis": "Original synthetic test content; not an approval for real materials",
        "evidence_url": "https://example.org/synthetic-test-only",
    }
    return {
        "schema_version": "0.1.0",
        "lesson_id": lesson_id,
        "title": title,
        "source_language": "en",
        "translation_language": "zh-CN",
        "media": {
            "source_url": "https://example.org/synthetic-video",
            "duration_ms": 4500,
            "access_mode": "external_link",
        },
        "segments": segments,
        "vocabulary": [
            {"headword": "public domain", "gloss": "公有领域", "segment_id": "s01", "token_ids": ["w03", "w04"]},
            {"headword": "bank", "gloss": "银行", "segment_id": "s02", "token_ids": ["w02"]},
            {"headword": "bank", "gloss": "河岸", "segment_id": "s03", "token_ids": ["w03"]},
        ],
        "provenance": {key: dict(rights) for key in ("media", "transcript", "translation", "vocabulary")},
    }


async def add_revision(
    db,
    lesson_id: str = "synthetic-learning",
    title: str = "Synthetic learning",
    *,
    status: str = "published",
    site: bool = True,
    external: bool = True,
    model: bool = True,
    current: bool = True,
) -> LessonRevision:
    lesson = await db.get(Lesson, lesson_id)
    if lesson is None:
        lesson = Lesson(id=lesson_id)
        db.add(lesson)
        await db.flush()
    pack = load_pack(json.dumps(synthetic_pack(lesson_id, title)).encode())
    revision = LessonRevision(
        lesson_id=lesson_id,
        fingerprint_version=FINGERPRINT_VERSION,
        fingerprint=fingerprint(pack),
        title=title,
        access_mode="external_link",
        pack=pack.model_dump(mode="json"),
        status=status,
        review={
            "uses": {
                key: {"approved": approved, "evidence": "synthetic engineering assertion only"}
                for key, approved in (
                    ("site_display", site),
                    ("external_redistribution", external),
                    ("model_processing", model),
                )
            }
        },
    )
    db.add(revision)
    await db.flush()
    if current:
        lesson.current_revision_id = revision.id
        await db.flush()
    return revision


def fixed_reference(revision: LessonRevision) -> dict:
    material_for_revision(revision)  # Fixtures themselves must satisfy the real reader.
    return {
        "lesson_id": revision.lesson_id,
        "revision_id": revision.id,
        "fingerprint_version": revision.fingerprint_version,
        "fingerprint": revision.fingerprint,
        "segment_id": "s01",
        "token_ids": ["w03", "w04"],
    }

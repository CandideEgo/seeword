"""P1 review diff and audit metadata: no pack mutation or persistence."""

import json
from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.schemas.lesson import ReviewLesson
from app.services.lesson_diff import diff_lesson_packs
from slcs import load_pack


def _pack():
    rights = {"attribution": "Synthetic fixture", "basis": "test only", "evidence_url": "https://example.org/rights"}
    document = {
        "schema_version": "0.1.0",
        "lesson_id": "p1-diff-test",
        "title": "Synthetic review fixture",
        "source_language": "en",
        "translation_language": "zh-CN",
        "media": {"source_url": "https://example.org/media", "duration_ms": 5000, "access_mode": "external_link"},
        "segments": [
            {
                "id": "s01",
                "start_ms": 0,
                "end_ms": 3000,
                "text": "We read books.",
                "translation": "我们读书。",
                "tokens": [
                    {"id": "w01", "start_char": 0, "end_char": 2, "timing": {"start_ms": 0, "end_ms": 500}},
                    {"id": "w02", "start_char": 3, "end_char": 7, "timing": {"start_ms": 500, "end_ms": 1000}},
                    {"id": "w03", "start_char": 8, "end_char": 13, "timing": {"start_ms": 1000, "end_ms": 2000}},
                ],
            }
        ],
        "vocabulary": [{"headword": "book", "gloss": "书", "segment_id": "s01", "token_ids": ["w03"]}],
        "provenance": {name: deepcopy(rights) for name in ("media", "transcript", "translation", "vocabulary")},
    }
    return _validated(document)


def _validated(document):
    return load_pack(json.dumps(document).encode()).model_dump(mode="json")


def test_diff_covers_content_timing_words_sources_and_media_without_changing_input():
    before = _pack()
    after = deepcopy(before)
    after["title"] = "Updated fixture"
    after["media"].update(
        source_url="https://youtube.com/watch?v=abcdefghijk", access_mode="provider_embed", duration_ms=6000
    )
    segment = after["segments"][0]
    segment.update(text="We read poems.", translation="我们读诗。", end_ms=3500, speaker="reader")
    segment["tokens"][2]["timing"]["end_ms"] = 2500
    after["vocabulary"][0].update(headword="poem", gloss="诗")
    after["provenance"]["transcript"]["basis"] = "updated synthetic evidence"
    after["provenance"]["changes"] = "Test correction, not a rights approval"
    after = _validated(after)
    snapshot = deepcopy((before, after))
    diff = diff_lesson_packs(before, after)
    assert set(diff["impacts"]) == {
        "metadata",
        "media",
        "original",
        "translation",
        "timing",
        "anchors",
        "vocabulary",
        "provenance",
    }
    changes = {change["path"]: change for change in diff["changes"]}
    assert changes["/segments/s01/text"]["before"] == "We read books."
    assert changes["/segments/s01/translation"]["after"] == "我们读诗。"
    assert changes["/segments/s01/end_ms"]["after"] == 3500
    assert changes["/segments/s01/tokens/w03/text"]["before"] == "books"
    assert changes["/segments/s01/tokens/w03/text"]["after"] == "poems"
    assert changes["/segments/s01/tokens/w03/timing"]["category"] == "timing"
    assert changes["/vocabulary/s01:w03/gloss"]["after"] == "诗"
    assert changes["/provenance/transcript/basis"]["category"] == "provenance"
    assert changes["/media/access_mode"]["after"] == "provider_embed"
    assert (before, after) == snapshot
    # Results are detached: a consumer cannot mutate either immutable input.
    changes["/segments/s01/tokens/w03/timing"]["before"]["end_ms"] = -1
    assert (before, after) == snapshot


def test_segment_and_token_identity_changes_are_additions_and_removals_not_list_offsets():
    before = _pack()
    renamed_token = deepcopy(before)
    renamed_token["segments"][0]["tokens"][2]["id"] = "word-new"
    renamed_token["vocabulary"][0]["token_ids"] = ["word-new"]
    diff = diff_lesson_packs(before, _validated(renamed_token))
    changes = {change["path"]: change for change in diff["changes"]}
    assert changes["/segments/s01/tokens/w03"]["kind"] == "removed"
    assert changes["/segments/s01/tokens/word-new"]["kind"] == "added"
    assert changes["/vocabulary/s01:w03"]["kind"] == "removed"
    assert changes["/vocabulary/s01:word-new"]["kind"] == "added"

    renamed_segment = deepcopy(before)
    renamed_segment["segments"][0]["id"] = "segment-new"
    renamed_segment["vocabulary"][0]["segment_id"] = "segment-new"
    diff = diff_lesson_packs(before, _validated(renamed_segment))
    changes = {change["path"]: change for change in diff["changes"]}
    assert changes["/segments/s01"]["kind"] == "removed"
    assert changes["/segments/segment-new"]["kind"] == "added"
    assert changes["/segments/segment-new"]["after"]["tokens"] == before["segments"][0]["tokens"]
    assert changes["/segments/@order"]["after"] == ["segment-new"]


def test_character_offsets_and_unicode_word_text_are_in_the_diff():
    before = _pack()
    after = deepcopy(before)
    after["segments"][0]["text"] = "🎬 We read books."
    for token in after["segments"][0]["tokens"]:
        token["start_char"] += 2
        token["end_char"] += 2
    diff = diff_lesson_packs(before, _validated(after))
    changes = {change["path"]: change for change in diff["changes"]}
    assert changes["/segments/s01/tokens/w01/start_char"]["after"] == 2
    assert changes["/segments/s01/tokens/w03/end_char"]["after"] == 15
    assert not any(path.endswith("/text") and "/tokens/" in path for path in changes)


def test_vocabulary_order_is_detected_and_diff_is_deterministic():
    before = _pack()
    before["vocabulary"].append({"headword": "read", "gloss": "读", "segment_id": "s01", "token_ids": ["w02"]})
    before = _validated(before)
    after = deepcopy(before)
    after["vocabulary"].reverse()
    diff = diff_lesson_packs(before, after)
    assert diff == {
        "impacts": ["vocabulary"],
        "changes": [
            {
                "category": "vocabulary",
                "kind": "modified",
                "path": "/vocabulary/@order",
                "before": ["s01:w03", "s01:w02"],
                "after": ["s01:w02", "s01:w03"],
            }
        ],
    }
    assert diff == diff_lesson_packs(dict(reversed(list(before.items()))), after)
    assert diff_lesson_packs(before, deepcopy(before)) == {"impacts": [], "changes": []}


def _review(**metadata):
    return ReviewLesson.model_validate(
        {
            "operation_id": "review-test",
            "source_commit": "a" * 40,
            "uses": {
                name: {"approved": name == "site_display", "evidence": "synthetic test only"}
                for name in ("site_display", "model_processing", "external_redistribution")
            },
            **metadata,
        }
    )


def test_review_metadata_allows_unknown_minutes_without_inventing_zero():
    assert _review().human_minutes is None
    review = _review(verification_method="  fixture comparison  ", limitations=" test only ", human_minutes=0)
    assert review.verification_method == "fixture comparison"
    assert review.limitations == "test only"
    assert review.human_minutes == 0


@pytest.mark.parametrize("minutes", [-1, float("nan"), float("inf"), True, "12"])
def test_review_metadata_rejects_invalid_minutes(minutes):
    with pytest.raises(ValidationError):
        _review(human_minutes=minutes)


@pytest.mark.parametrize("field", ["verification_method", "limitations"])
def test_review_metadata_rejects_blank_or_unbounded_evidence(field):
    for value in ("   ", "x" * 4001):
        with pytest.raises(ValidationError):
            _review(**{field: value})

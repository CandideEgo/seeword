import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.services.video_learning_material import load_video_material
from app.slcs import PackValidationError, json_schema, load_pack

_BACKEND = Path(__file__).resolve().parents[1]
_SPEC = _BACKEND.parent / "docs" / "slcs"
_EXAMPLE = _SPEC / "examples" / "welcome-to-wikisource.json"
_MISSING = object()


@pytest.fixture
def document():
    return json.loads(_EXAMPLE.read_bytes())


def _payload(document):
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


def test_real_example_resolves_a_vocabulary_occurrence():
    material = load_video_material(_EXAMPLE.read_bytes())
    assert material.kind == "video"
    assert material.lesson_id == "welcome-to-wikisource"
    assert material.media.access_mode == "external_link"
    assert material.media.duration_ms == 49_453
    occurrence = next(entry for entry in material.vocabulary if entry.headword == "public domain")
    assert occurrence.text == "public domain"
    segment = next(segment for segment in material.segments if segment.id == occurrence.segment_id)
    words = [token for token in segment.tokens if token.id in occurrence.token_ids]
    assert words[0].timing is not None
    assert words[-1].timing is not None
    assert segment.start_ms < occurrence.start_ms == words[0].timing.start_ms
    assert occurrence.end_ms == words[-1].timing.end_ms < segment.end_ms
    assert segment.translation
    assert "CC BY-SA 4.0" in material.provenance.media.basis
    with pytest.raises(FrozenInstanceError):
        material.title = "replacement"  # type: ignore[misc]


def test_unaligned_middle_word_falls_back_to_segment(document):
    segment = next(segment for segment in document["segments"] if len(segment["tokens"]) >= 5)
    tokens = segment["tokens"]
    tokens[1]["timing"] = None
    document["vocabulary"] = [
        {
            "headword": "test phrase",
            "gloss": "测试",
            "segment_id": segment["id"],
            "token_ids": [token["id"] for token in tokens[:3]],
        }
    ]
    material = load_video_material(_payload(document))
    occurrence = material.vocabulary[0]
    assert (occurrence.start_ms, occurrence.end_ms) == (segment["start_ms"], segment["end_ms"])
    projected = next(item for item in material.segments if item.id == segment["id"])
    assert projected.tokens[1].timing is None


def test_fingerprint_ignores_json_layout_and_tracks_content_changes(document):
    material = load_video_material(_EXAMPLE.read_bytes())
    reordered = json.dumps(document, sort_keys=True, indent=2).encode("utf-8")
    assert load_video_material(reordered).source_fingerprint == material.source_fingerprint
    document["segments"][0]["translation"] += "！"
    updated = load_video_material(_payload(document))
    assert updated.source_fingerprint != material.source_fingerprint
    assert updated.lesson_id == material.lesson_id


def test_token_offsets_use_unicode_code_points(document):
    segment = document["segments"][0]
    segment["text"] = "🎬 We’re café-ready!"
    segment["tokens"] = [
        {"id": "t1", "start_char": 2, "end_char": 7, "timing": {"start_ms": 1000, "end_ms": 1300}},
        {"id": "t2", "start_char": 8, "end_char": 18, "timing": {"start_ms": 1300, "end_ms": 1600}},
    ]
    segment["start_ms"], segment["end_ms"] = 900, 2000
    document["segments"] = [segment]
    document["vocabulary"] = [
        {"headword": "café-ready", "gloss": "准备就绪", "segment_id": segment["id"], "token_ids": ["t2"]}
    ]
    material = load_video_material(_payload(document))
    assert material.vocabulary[0].text == "café-ready"


@pytest.mark.parametrize(
    ("location", "value", "diagnostic"),
    [
        (("segments", 0, "translation"), _MISSING, "/segments/0/translation"),
        (("segments", 0, "translation"), "   ", "/segments/0/translation"),
        (("vocabulary",), [], "/vocabulary"),
        (("segments", 0, "tokens", 0, "timing"), None, "80%"),
        (("segments", 0, "tokens", 0, "timing", "end_ms"), 99_000, "/segments/0/tokens/0/timing"),
        (("segments", 0, "tokens", 0, "start_char"), 1, "/segments/0/tokens/0"),
        (("segments", 0, "end_ms"), 99_000, "/segments/0"),
        (("vocabulary", 0, "segment_id"), "missing", "/vocabulary/0/segment_id"),
        (("vocabulary", 0, "token_ids"), ["missing"], "/vocabulary/0/token_ids"),
        (("media", "source_url"), "http://example.com/video", "/media/source_url"),
        (("media", "source_url"), "https://a@example.com/video", "/media/source_url"),
        (("media", "source_url"), "https://%", "/media/source_url"),
        (("media", "source_url"), "https://exa<mple.com", "/media/source_url"),
        (("provenance", "translation"), _MISSING, "/provenance/translation"),
        (("schema_version",), "0.2.0", "/schema_version"),
    ],
)
def test_invalid_pack_has_the_same_diagnostic_for_both_consumers(document, location, value, diagnostic):
    target = document
    for field in location[:-1]:
        target = target[field]
    if value is _MISSING:
        del target[location[-1]]
    else:
        target[location[-1]] = value
    for reader in (load_pack, load_video_material):
        with pytest.raises(PackValidationError, match=diagnostic):
            reader(_payload(document))


def test_embedding_requires_an_official_youtube_watch_page(document):
    document["media"]["access_mode"] = "provider_embed"
    document["media"]["source_url"] = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert load_pack(_payload(document)).media.access_mode == "provider_embed"
    document["media"]["source_url"] = "https://www.youtube.com.example.com/watch?v=dQw4w9WgXcQ"
    with pytest.raises(PackValidationError, match="/media/source_url"):
        load_pack(_payload(document))


def test_invalid_encoding_and_duplicate_json_keys_are_rejected():
    with pytest.raises(PackValidationError, match="UTF-8 JSON"):
        load_pack(b"\xff")
    with pytest.raises(PackValidationError, match="duplicate JSON key"):
        load_pack(b'{"lesson_id":"one","lesson_id":"two"}')


def test_checked_in_schema_matches_the_generated_contract():
    generated = json_schema()
    assert generated["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert json.loads((_SPEC / "schema.json").read_bytes()) == generated


def test_cli_reports_success_and_rejects_invalid_file(tmp_path):
    command = [sys.executable, "-m", "app.slcs", "validate"]
    valid = subprocess.run([*command, str(_EXAMPLE)], cwd=_BACKEND, capture_output=True, check=False)
    assert valid.returncode == 0, valid.stderr
    assert b"welcome-to-wikisource" in valid.stdout
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"{}")
    invalid = subprocess.run([*command, str(bad)], cwd=_BACKEND, capture_output=True, check=False)
    assert invalid.returncode == 1
    assert b"/schema_version" in invalid.stderr

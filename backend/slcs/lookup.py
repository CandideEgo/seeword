"""Shared structured vocabulary and subtitle results."""

from dataclasses import asdict

from .material import VideoLearningMaterial, resolve_vocabulary


def lookup(
    material: VideoLearningMaterial, headword: str, allowed_segments: set[str] | None = None
) -> dict[str, object]:
    segments = {segment.id: segment for segment in material.segments}
    occurrences = resolve_vocabulary(material, headword, segment_ids=allowed_segments)
    return {
        "lesson_id": material.lesson_id,
        "fingerprint": material.source_fingerprint,
        "matches": [
            {
                **asdict(entry),
                "sentence": segments[entry.segment_id].text,
                "translation": segments[entry.segment_id].translation,
            }
            for entry in occurrences
        ],
    }

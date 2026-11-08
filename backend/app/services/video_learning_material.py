"""Read-only video material projection for SeeWord V2."""

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from app.slcs import Media, Provenance, Segment, load_pack


@dataclass(frozen=True)
class VocabularyOccurrence:
    headword: str
    gloss: str
    segment_id: str
    token_ids: tuple[str, ...]
    text: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class VideoLearningMaterial:
    kind: Literal["video"]
    lesson_id: str
    source_fingerprint: str
    title: str
    source_language: Literal["en"]
    translation_language: Literal["zh-CN"]
    media: Media
    segments: tuple[Segment, ...]
    vocabulary: tuple[VocabularyOccurrence, ...]
    provenance: Provenance


def load_video_material(payload: bytes) -> VideoLearningMaterial:
    """Validate an SLCS document and resolve its vocabulary occurrences."""
    pack = load_pack(payload)
    canonical = json.dumps(pack.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    segments = {segment.id: segment for segment in pack.segments}
    tokens = {segment.id: {token.id: token for token in segment.tokens} for segment in pack.segments}
    vocabulary = []
    for entry in pack.vocabulary:
        segment = segments[entry.segment_id]
        referenced = [tokens[entry.segment_id][token_id] for token_id in entry.token_ids]
        first, last = referenced[0], referenced[-1]
        start, end = segment.start_ms, segment.end_ms
        if (
            first.timing is not None
            and last.timing is not None
            and all(token.timing is not None for token in referenced)
        ):
            start, end = first.timing.start_ms, last.timing.end_ms
        vocabulary.append(
            VocabularyOccurrence(
                headword=entry.headword,
                gloss=entry.gloss,
                segment_id=segment.id,
                token_ids=entry.token_ids,
                text=segment.text[first.start_char : last.end_char],
                start_ms=start,
                end_ms=end,
            )
        )
    return VideoLearningMaterial(
        kind="video",
        lesson_id=pack.lesson_id,
        source_fingerprint=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        title=pack.title,
        source_language=pack.source_language,
        translation_language=pack.translation_language,
        media=pack.media,
        segments=pack.segments,
        vocabulary=tuple(vocabulary),
        provenance=pack.provenance,
    )

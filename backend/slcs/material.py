"""Read-only video material, vocabulary occurrences and content fingerprints."""

import hashlib
import json
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Literal

from .contract import FINGERPRINT_VERSION, LearningPack, Media, Provenance, Segment, load_pack


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


def stable_hash(value: object) -> str:
    """Return the SHA-256 digest of canonical UTF-8 JSON."""
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fingerprint(pack: LearningPack) -> str:
    """Hash a validated pack, including contract defaults and the fingerprint version."""
    return stable_hash({"fingerprint_version": FINGERPRINT_VERSION, "pack": pack.model_dump(mode="json")})


def resolve_vocabulary(
    material: VideoLearningMaterial,
    headword: str,
    *,
    segment_ids: Collection[str] | None = None,
) -> tuple[VocabularyOccurrence, ...]:
    """Find all matching occurrences in pack order, optionally limited to selected segments."""
    query = headword.strip().casefold()
    return tuple(
        entry
        for entry in material.vocabulary
        if entry.headword.strip().casefold() == query and (segment_ids is None or entry.segment_id in segment_ids)
    )


def resolve_anchor(segment: Segment, token_ids: Sequence[str]) -> tuple[str, int, int]:
    """Resolve consecutive token IDs to their exact surface text and time range."""
    positions = {token.id: index for index, token in enumerate(segment.tokens)}
    try:
        indices = [positions[token_id] for token_id in token_ids]
    except KeyError:
        raise ValueError("unknown token ID") from None
    if not indices or indices != list(range(indices[0], indices[0] + len(indices))):
        raise ValueError("expected consecutive tokens in text order")
    tokens = segment.tokens[indices[0] : indices[-1] + 1]
    first, last = tokens[0], tokens[-1]
    start, end = segment.start_ms, segment.end_ms
    if first.timing is not None and last.timing is not None and all(token.timing is not None for token in tokens):
        start, end = first.timing.start_ms, last.timing.end_ms
    return segment.text[first.start_char : last.end_char], start, end


def load_video_material(payload: bytes) -> VideoLearningMaterial:
    """Validate an SLCS document and resolve its vocabulary occurrences."""
    pack = load_pack(payload)
    segments = {segment.id: segment for segment in pack.segments}
    vocabulary = []
    for entry in pack.vocabulary:
        segment = segments[entry.segment_id]
        text, start, end = resolve_anchor(segment, entry.token_ids)
        vocabulary.append(
            VocabularyOccurrence(
                headword=entry.headword,
                gloss=entry.gloss,
                segment_id=segment.id,
                token_ids=entry.token_ids,
                text=text,
                start_ms=start,
                end_ms=end,
            )
        )
    return VideoLearningMaterial(
        kind="video",
        lesson_id=pack.lesson_id,
        source_fingerprint=fingerprint(pack),
        title=pack.title,
        source_language=pack.source_language,
        translation_language=pack.translation_language,
        media=pack.media,
        segments=pack.segments,
        vocabulary=tuple(vocabulary),
        provenance=pack.provenance,
    )

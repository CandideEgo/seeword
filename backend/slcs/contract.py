"""SLCS v0.1 data contract and offline validation."""

import json
import re
from typing import Annotated, Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    ValidationError,
)

#: Bumped whenever a change to this contract would alter the fingerprint
#: of an otherwise unchanged pack; mirrors the normalization-version field
#: on the content revisions that will store these digests.
FINGERPRINT_VERSION = "slcs-pack-v1"

NonBlank = Annotated[str, StringConstraints(pattern=r"\S")]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
NonNegative = Annotated[StrictInt, Field(ge=0)]
Positive = Annotated[StrictInt, Field(gt=0)]

# Keep contractions and hyphenated words together, including Latin combining marks.
_WORD_PART = r"[^\W_](?:[^\W_]|[\u0300-\u036f])*"
_WORD = re.compile(rf"{_WORD_PART}(?:['’-]{_WORD_PART})*")
_YOUTUBE_ID = re.compile(r"[A-Za-z0-9_-]{11}")


def tokenize(text: str) -> tuple[tuple[int, int], ...]:
    """Return the v0.1 word spans as half-open Unicode code point offsets."""
    return tuple(match.span() for match in _WORD.finditer(text))


def _validate_https_url(value: str) -> str:
    try:
        parsed = AnyHttpUrl(value)
    except ValidationError:
        raise ValueError("expected a valid HTTPS URL") from None
    authority = urlsplit(value)
    if not authority.hostname or authority.username is not None or parsed.port == 0:
        raise ValueError("expected an HTTPS URL with a host, no credentials and a valid port")
    return value


HttpsUrl = Annotated[
    str,
    StringConstraints(pattern=r"^https://[^\s\x00-\x1f\x7f\\]+$"),
    AfterValidator(_validate_https_url),
]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Media(_Model):
    source_url: HttpsUrl
    duration_ms: Positive
    access_mode: Literal["external_link", "provider_embed"]


class TimeRange(_Model):
    start_ms: NonNegative
    end_ms: Positive


class Token(_Model):
    id: Slug
    start_char: NonNegative
    end_char: Positive
    timing: TimeRange | None


class Segment(TimeRange):
    id: Slug
    text: NonBlank
    translation: NonBlank
    tokens: Annotated[tuple[Token, ...], Field(min_length=1)]
    speaker: NonBlank | None = None


class VocabularyEntry(_Model):
    headword: NonBlank
    gloss: NonBlank
    segment_id: Slug
    token_ids: Annotated[tuple[Slug, ...], Field(min_length=1)]


class Rights(_Model):
    attribution: NonBlank
    basis: NonBlank
    evidence_url: HttpsUrl


class Provenance(_Model):
    media: Rights
    transcript: Rights
    translation: Rights
    vocabulary: Rights
    changes: NonBlank | None = None


class LearningPack(_Model):
    schema_version: Literal["0.1.0"]
    lesson_id: Slug
    title: NonBlank
    source_language: Literal["en"]
    translation_language: Literal["zh-CN"]
    media: Media
    segments: Annotated[tuple[Segment, ...], Field(min_length=1)]
    vocabulary: Annotated[tuple[VocabularyEntry, ...], Field(min_length=1)]
    provenance: Provenance


class PackValidationError(ValueError):
    """A malformed or nonconforming SLCS document."""

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def _check_embed(media: Media) -> None:
    if media.access_mode == "external_link":
        return
    parsed = urlsplit(media.source_url)
    video_ids = parse_qs(parsed.query, keep_blank_values=True).get("v", [])
    if (
        parsed.netloc.lower() not in {"www.youtube.com", "youtube.com"}
        or parsed.path != "/watch"
        or len(video_ids) != 1
        or not _YOUTUBE_ID.fullmatch(video_ids[0])
    ):
        raise PackValidationError("/media/source_url", "provider_embed requires a YouTube watch URL with one video ID")


def _check_segment(segment: Segment, path: str) -> dict[str, int]:
    word_spans = tokenize(segment.text)
    if len(segment.tokens) != len(word_spans):
        raise PackValidationError(f"{path}/tokens", "expected one token per word in text")

    positions: dict[str, int] = {}
    aligned_count = 0
    previous_end = segment.start_ms
    for index, (token, word_span) in enumerate(zip(segment.tokens, word_spans, strict=True)):
        token_path = f"{path}/tokens/{index}"
        if token.id in positions:
            raise PackValidationError(f"{token_path}/id", "duplicate token ID")
        positions[token.id] = index
        if (token.start_char, token.end_char) != word_span:
            raise PackValidationError(token_path, f"expected word interval {word_span}")
        if token.timing is None:
            continue
        start, end = token.timing.start_ms, token.timing.end_ms
        if not previous_end <= start < end <= segment.end_ms:
            raise PackValidationError(f"{token_path}/timing", "times must be ordered, disjoint and inside the segment")
        previous_end = end
        aligned_count += 1
    if aligned_count * 5 < len(segment.tokens) * 4:
        raise PackValidationError(f"{path}/tokens", "at least 80% of words must have timing")
    return positions


def _check_pack(pack: LearningPack) -> None:
    _check_embed(pack.media)
    segments: dict[str, dict[str, int]] = {}
    previous_end = 0
    for index, segment in enumerate(pack.segments):
        path = f"/segments/{index}"
        if segment.id in segments:
            raise PackValidationError(f"{path}/id", "duplicate segment ID")
        if not previous_end <= segment.start_ms < segment.end_ms <= pack.media.duration_ms:
            raise PackValidationError(path, "segment times must be ordered, disjoint and inside the media duration")
        previous_end = segment.end_ms
        segments[segment.id] = _check_segment(segment, path)

    occurrences: set[tuple[str, tuple[str, ...]]] = set()
    for index, entry in enumerate(pack.vocabulary):
        path = f"/vocabulary/{index}"
        positions = segments.get(entry.segment_id)
        if positions is None:
            raise PackValidationError(f"{path}/segment_id", "unknown segment ID")
        try:
            indices = [positions[token_id] for token_id in entry.token_ids]
        except KeyError as exc:
            raise PackValidationError(f"{path}/token_ids", f"unknown token ID {exc.args[0]!r}") from None
        if indices != list(range(indices[0], indices[0] + len(indices))):
            raise PackValidationError(f"{path}/token_ids", "expected consecutive tokens in text order")
        # The same word span may only be described once: two glosses for one
        # occurrence would leave the reader (and any stored revision) without a
        # single authoritative definition. Distinct spans of one headword stay
        # legal — that is the multi-context case the schema is meant to carry.
        occurrence = (entry.segment_id, entry.token_ids)
        if occurrence in occurrences:
            raise PackValidationError(path, "duplicate vocabulary entry for the same word span")
        occurrences.add(occurrence)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PackValidationError("/", f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_pack(payload: bytes) -> LearningPack:
    """Read one UTF-8 JSON document and enforce the complete SLCS v0.1 contract."""
    try:
        document = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except PackValidationError:
        raise
    except (ValueError, RecursionError) as exc:
        raise PackValidationError("/", f"expected UTF-8 JSON ({exc})") from None
    try:
        pack = LearningPack.model_validate(document)
    except ValidationError as exc:
        issue = exc.errors(include_input=False, include_url=False)[0]
        path = "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in issue["loc"])
        raise PackValidationError(path, issue["msg"]) from None
    _check_pack(pack)
    return pack


def json_schema() -> dict[str, object]:
    """Return the structural schema. Cross-field checks live in load_pack."""
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **LearningPack.model_json_schema()}

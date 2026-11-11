"""Backward-compatible import path for the independent SLCS reader."""

from slcs import (
    FINGERPRINT_VERSION,
    HttpsUrl,
    LearningPack,
    Media,
    NonBlank,
    NonNegative,
    PackValidationError,
    Positive,
    Provenance,
    Rights,
    Segment,
    Slug,
    TimeRange,
    Token,
    VocabularyEntry,
    fingerprint,
    json_schema,
    load_pack,
    tokenize,
)

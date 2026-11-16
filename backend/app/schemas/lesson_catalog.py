"""Portable references are API envelopes, never fields of an SLCS v0.1 pack."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

MAX_ANCHOR_ID_LENGTH = 100
MAX_ANCHOR_TOKENS = 128

Identifier = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=100)]
AnchorId = Annotated[
    str, StringConstraints(strict=True, max_length=MAX_ANCHOR_ID_LENGTH, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
]


class MaterialIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lesson_id: Identifier
    fingerprint_version: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=32)]
    fingerprint: Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{64}$")]
    revision_id: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=36)] | None = None


class FixedReference(MaterialIdentity):
    segment_id: AnchorId
    token_ids: Annotated[list[AnchorId], Field(min_length=1, max_length=MAX_ANCHOR_TOKENS)]

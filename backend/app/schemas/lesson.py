"""Write contracts for SLCS lessons and their publication workflow."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

LessonUse = Literal["site_display", "model_processing", "external_redistribution"]
OperationId = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^\S+$")]
RevisionId = Annotated[str, StringConstraints(min_length=1, max_length=36)]
Evidence = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4_000)]


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Operation(_Input):
    operation_id: OperationId


class ImportLesson(_Operation):
    pack_json: str


class UseReview(_Input):
    approved: bool = Field(strict=True)
    evidence: Evidence


class LessonUses(_Input):
    site_display: UseReview
    model_processing: UseReview
    external_redistribution: UseReview


class ReviewLesson(_Operation):
    source_commit: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
    uses: LessonUses


class PublishLesson(_Operation):
    expected_current_revision_id: RevisionId | None
    receipt: str = Field(min_length=1, max_length=16_384, repr=False)


class WithdrawLesson(_Operation):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1_000)]


class SaveLessonProgress(_Input):
    revision_id: RevisionId
    position_ms: int = Field(ge=0, le=2**63 - 1, strict=True)


class RecordLessonActivity(_Input):
    revision_id: RevisionId
    event_id: OperationId
    event_type: Literal["watch_time", "complete"]
    delta_s: float | None = Field(default=None, gt=0, le=120, allow_inf_nan=False, strict=True)

    @model_validator(mode="after")
    def check_delta(self):
        if (self.event_type == "watch_time") != (self.delta_s is not None):
            raise ValueError("delta_s is required only for watch_time events")
        return self

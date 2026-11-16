"""No caller-provided identity, free-form commands or self-reported confirmation."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints, model_validator

from app.schemas.lesson_catalog import FixedReference, Identifier

OperationId = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Za-z0-9_.:-]{1,64}$")]
PositivePosition = Annotated[int, Field(strict=True, ge=0, le=2**63 - 1)]


class ResourceLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lesson_ids: list[Identifier] = Field(default_factory=list, max_length=200)
    word_ids: list[Identifier] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def explicit_resources(self) -> Self:
        if not self.lesson_ids and not self.word_ids:
            raise ValueError("至少明确授权一个课程或本人词条")
        if len(set(self.lesson_ids)) != len(self.lesson_ids) or len(set(self.word_ids)) != len(self.word_ids):
            raise ValueError("授权资源不能重复")
        return self


class SaveVocabulary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: OperationId
    reference: FixedReference


class SaveProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: OperationId
    revision_id: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=36)]
    position_ms: PositivePosition
    expected_version: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=40)]


class PrepareIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: OperationId
    action: Literal["review", "complete"]
    word_id: Identifier | None = None
    lesson_id: Identifier | None = None
    revision_id: Annotated[str, StringConstraints(strict=True, min_length=1, max_length=36)] | None = None
    quality: Annotated[int, Field(strict=True, ge=0, le=5)] | None = None

    @model_validator(mode="after")
    def action_parameters(self) -> Self:
        if self.action == "review":
            if (
                self.word_id is None
                or self.quality is None
                or self.lesson_id is not None
                or self.revision_id is not None
            ):
                raise ValueError("review 仅接受 word_id 与 quality")
        elif self.lesson_id is None or self.revision_id is None or self.word_id is not None or self.quality is not None:
            raise ValueError("complete 仅接受 lesson_id 与 revision_id")
        return self


class ConfirmIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: StrictBool

    @model_validator(mode="after")
    def affirmative(self) -> Self:
        if self.confirmed is not True:
            raise ValueError("必须明确确认此操作")
        return self

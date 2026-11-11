from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class VocabularyResponse(BaseModel):
    id: str
    word: str
    definition: str | None = None
    translation: str | None = None
    part_of_speech: str | None = None
    ipa: str | None = None
    example_sentences: list[str] | None = None
    collocations: list[str] | None = None
    difficulty_level: str | None = None
    mastery_level: str
    context_sentence: str | None = None
    video_id: str | None = None
    # Display-only enrichment filled by vocabulary_service.attach_word_sources:
    # the word row shows "来源视频 · mm:ss" instead of a bare link.
    video_title: str | None = None
    subtitle_start_time: float | None = None
    has_lesson_sources: bool = False
    review_operations_enabled: bool = False
    # Phase 1 D3b: drill "回看原句" needs the originating subtitle; null when
    # the word was added before the column existed (no source shown).
    subtitle_id: str | None = None
    review_count: int
    next_review_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VocabularyEnrichResponse(BaseModel):
    id: str
    word: str
    definition: str
    translation: str
    part_of_speech: str
    ipa: str
    example_sentences: list[str]
    collocations: list[str]
    difficulty_level: str

    model_config = {"from_attributes": True}


class QuizGenerateRequest(BaseModel):
    quiz_type: Literal["multiple_choice", "spelling", "context_fill", "translation"]
    count: int = Field(default=10, ge=1, le=30)
    due_only: bool = False


class QuizQuestionResponse(BaseModel):
    id: str
    word: str
    quiz_type: str
    question: str
    options: list[str] | None = None
    correct_answer_index: int | None = None


class QuizAnswerItem(BaseModel):
    question_id: str
    answer: str


class QuizSubmitRequest(BaseModel):
    answers: list[QuizAnswerItem]


class QuizItemResult(BaseModel):
    question_id: str
    correct: bool
    correct_answer: str
    user_answer: str


class QuizSubmitResponse(BaseModel):
    score: int
    total: int
    results: list[QuizItemResult]


class VocabularyStatsResponse(BaseModel):
    total: int
    new_count: int
    learning_count: int
    reviewing_count: int
    mastered_count: int
    # Legacy badge count (folds new words in). UI uses due_review_count.
    due_count: int
    # Due words in the review queue only (excludes new/mastered); identical to
    # daily-session.totals.due_total.
    due_review_count: int


# ---------------------------------------------------------------------------
# Daily quota (DEC-053)
# ---------------------------------------------------------------------------


class VocabularyPreferencesResponse(BaseModel):
    """The user's daily training quota, global per user (not per video)."""

    daily_new_target: int
    daily_review_target: int
    quota_min: int
    quota_max: int


class VocabularyPreferencesUpdate(BaseModel):
    """Partial update; ``None`` leaves a field untouched.

    Bounds live here rather than in the service so a bad request is a 422 with
    a field path, not a silently clamped value.
    """

    daily_new_target: int | None = Field(default=None, ge=5, le=100)
    daily_review_target: int | None = Field(default=None, ge=5, le=100)


class TodayTrainingSummary(BaseModel):
    """今日累计：含加练的已学词数 + 已开始的轮数（今日 tab 的「第 K 轮」）。"""

    words_learned: int
    rounds: int


# ---------------------------------------------------------------------------
# Study rounds (DEC-053)
# ---------------------------------------------------------------------------


class StudySessionItemResponse(BaseModel):
    id: str
    vocabulary_id: str
    sort_order: int
    correct_streak: int
    wrong_in_round: bool
    status: Literal["pending", "learning", "graduated"]
    # None when the vocabulary row is gone; the client drops such items.
    word: VocabularyResponse | None = None


class StudySessionResponse(BaseModel):
    id: str
    kind: Literal["daily", "extra"]
    local_date: date
    target_count: int
    done_count: int
    correct_count: int
    status: Literal["active", "finished", "abandoned"]
    items: list[StudySessionItemResponse]


class StudySessionEnvelope(BaseModel):
    """Round payload for the 取/建 endpoints.

    ``session`` is None when there is nothing left to learn — a normal state
    (the client falls through to the review phase), not an error.
    """

    session: StudySessionResponse | None = None
    today: TodayTrainingSummary


class StudySessionStartRequest(BaseModel):
    kind: Literal["daily", "extra"] = "daily"


class StudySessionAnswerRequest(BaseModel):
    vocabulary_id: str
    correct: bool


class StudySessionAnswerResponse(BaseModel):
    item: StudySessionItemResponse
    session_id: str
    done_count: int
    correct_count: int
    target_count: int
    session_status: Literal["active", "finished", "abandoned"]
    graduated: bool
    today: TodayTrainingSummary


# ---------------------------------------------------------------------------
# Response schemas (BE-07: daily-session / practice / word actions were dicts)
# ---------------------------------------------------------------------------


class DailySessionTotals(BaseModel):
    new_total: int
    due_total: int


class TrainingPreview(BaseModel):
    active_session_id: str | None = None
    new_words: list[VocabularyResponse]
    review_words: list[VocabularyResponse]


class DailySessionResponse(BaseModel):
    training_preview: TrainingPreview
    new_words: list[VocabularyResponse]
    review_words: list[VocabularyResponse]
    totals: DailySessionTotals
    preferences: VocabularyPreferencesResponse
    today: TodayTrainingSummary


class VocabularyAddResponse(BaseModel):
    id: str
    word: str
    context_sentence: str | None = None
    video_id: str | None = None
    subtitle_id: str | None = None
    created_at: str


class VocabularyReviewResponse(BaseModel):
    id: str
    word: str
    next_review_at: str
    interval_days: int
    review_count: int
    wrong_count: int
    last_wrong_at: str | None = None


class VocabularyMasteredResponse(BaseModel):
    id: str
    word: str
    mastery_level: str


class VocabularyDeleteResponse(BaseModel):
    success: bool


class LearningWordsResponse(BaseModel):
    words: list[str]


class WatchContextVocabSet(BaseModel):
    """The set already collected from this video.

    The watch page only needs the id (to open it) and knows the video it is on,
    so the full ``VocabSet`` card shape (title, counts, thumbnail) is not built
    here — that would turn one lightweight lookup into the whole ``/vocab-sets``
    aggregation.
    """

    id: str
    video_id: str | None = None


class WatchContextResponse(BaseModel):
    """Everything the watch page needs about the viewer's vocabulary, in one call."""

    learning_words: list[str]
    mastered_words: list[str]
    vocab_set: WatchContextVocabSet | None = None


class PracticeItem(BaseModel):
    word: str
    category: str
    type: str
    translation: str | None = None
    options: list[str] | None = None
    answer: str | None = None
    phonetic: str | None = None
    sentence_template: str | None = None
    full_sentence: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    video_id: str | None = None
    subtitle_id: str | None = None


class VocabularyPracticeResponse(BaseModel):
    items: list[PracticeItem]

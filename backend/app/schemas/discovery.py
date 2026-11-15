"""Discovery response contracts for search, dictionary, sets and learner actions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.channel import ChannelCard, LatestVideo
from app.schemas.exam import ExamAttemptCreateResponse
from app.schemas.pagination import PaginatedResponse
from app.schemas.video import VideoResponse


class ContinueVideo(LatestVideo):
    progress_percentage: float
    position_seconds: float | None = None


class ChannelSubscriptionCard(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None = None
    cover_url: str | None = None
    video_count: int
    latest_video: LatestVideo | None = None
    continue_video: ContinueVideo | None = None
    unlearned_count: int


class SubscriptionState(BaseModel):
    subscribed: bool


class SentenceFavoriteItem(BaseModel):
    id: str
    subtitle_id: str
    video_id: str
    title: str
    text_en: str
    text_zh: str | None = None
    start_time: float | None = None
    available: bool
    created_at: datetime


class SentenceFavoriteStatus(BaseModel):
    saved: bool


class DictionaryWord(BaseModel):
    """One ECDICT row. Extra keys (frequency rank etc.) are preserved."""

    model_config = ConfigDict(extra="allow")

    lemma: str
    phonetic: str | None = None
    translation: str | None = None
    pos: str | None = None
    levels: list[str] = []
    bnc: int = 0


class DictionaryResponse(PaginatedResponse[DictionaryWord]):
    pass


class MetadataSampleWord(BaseModel):
    word: str
    phonetic: str | None = None
    translation: str | None = None
    levels: list[str]


class WordTimestamp(BaseModel):
    model_config = ConfigDict(extra="allow")

    word: str | None = None
    start: float | None = None
    end: float | None = None


class LearningMetadataItem(BaseModel):
    subtitle_count: int
    exam_word_count: int
    sample_text_en: str | None = None
    sample_text_zh: str | None = None
    sample_words: list[MetadataSampleWord]
    sample_subtitle_id: str
    sample_start_time: float | None = None
    sample_end_time: float | None = None
    sample_word_timestamps: list[WordTimestamp]


class SetCreatedResponse(BaseModel):
    id: str


class SetRenamedResponse(BaseModel):
    id: str
    name: str


class SetDeletedResponse(BaseModel):
    deleted: bool


class SetWordsAddedResponse(BaseModel):
    added: int


class SetWordRemovedResponse(BaseModel):
    removed: bool


# ---------------------------------------------------------------------------
# Search / daily recommendation
# ---------------------------------------------------------------------------


class SearchVideoGroup(BaseModel):
    items: list[VideoResponse]
    has_more: bool


class SearchSubtitleItem(BaseModel):
    id: str
    text_en: str
    text_zh: str | None = None
    start_time: float
    video: VideoResponse


class SearchSubtitleGroup(BaseModel):
    items: list[SearchSubtitleItem]
    has_more: bool


class SearchChannelGroup(BaseModel):
    items: list[ChannelCard]
    has_more: bool


class SearchResponse(BaseModel):
    """Only the requested groups are present (route uses exclude_unset)."""

    videos: SearchVideoGroup | None = None
    subtitles: SearchSubtitleGroup | None = None
    words: DictionaryResponse | None = None
    channels: SearchChannelGroup | None = None


class DailyPreviewResponse(BaseModel):
    token: str
    title: str
    level: str
    reason: str
    question_type: str
    question_count: int
    group_count: int
    variant: int
    passage: str | None = None


class PracticeSummaryRecent(BaseModel):
    id: str
    title: str
    correct: int
    total: int
    submitted_at: datetime | None = None


class PracticeSummaryResponse(BaseModel):
    types: dict[str, dict[str, int]]
    recent: list[PracticeSummaryRecent]


class DailyStartResponse(ExamAttemptCreateResponse):
    pass

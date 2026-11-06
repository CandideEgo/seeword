from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exam_levels import validate_word_levels


class VideoCreate(BaseModel):
    source_url: str

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("URL too long (max 500 characters)")
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Only HTTP/HTTPS URLs are allowed")
        return v


# Max description characters carried by list/feed responses (home, browse,
# rankings). Detail responses keep the full description. YouTube descriptions
# can be several KB; a page of 20 cards must not balloon because of them.
CARD_DESCRIPTION_LIMIT = 200


class VideoResponse(BaseModel):
    id: str
    title: str
    title_zh: str | None = None
    source_url: str
    video_source: str
    thumbnail_url: str | None
    duration: float | None
    difficulty_level: str | None
    status: str
    topic_tags: str | None
    is_official: bool
    is_published: bool = False
    # UGC review lifecycle (draft/pending_review/published/rejected). Exposed so
    # the owner's "my videos" list and the admin queue can badge status.
    review_status: str = "draft"
    # Admin's rejection reason (set when review_status == rejected). Visible to
    # the owner so they can fix and resubmit; null for everyone else. The
    # service layer zeroes it out for non-owner detail reads.
    rejection_reason: str | None = None
    video_url_480p: str | None = None
    video_url_720p: str | None = None
    video_url_1080p: str | None = None
    processing_mode: str | None = None
    processing_step: str | None = None
    processing_progress: int = 0
    # Error message from the processing pipeline. The service layer zeroes it
    # out for non-owners (same pattern as rejection_reason) so the public never
    # sees internal error details, but the owner can tell *why* their video failed.
    error_message: str | None = None
    like_count: int = 0
    favorite_count: int = 0
    # In-app play-completion counter (behavior_service on `complete`), distinct
    # from ext_view_count (YouTube-side). Home/browse cards show the totals.
    view_count: int = 0
    # P1 learning_score (0-100, null until first computed). Drives list
    # sorting; full per-factor breakdown via the admin score endpoint.
    score: float | None = None
    score_updated_at: str | None = None
    # ── External (YouTube) metadata + speech metrics (阶段 1/3) ──
    # Null for local videos / before extraction. ext_* counts are YouTube-side
    # (distinct from the in-app like/view counters above).
    yt_video_id: str | None = None
    channel_name: str | None = None
    # Video description (Video.description property → external_meta); null for
    # local/unextracted videos. List serializers truncate to
    # CARD_DESCRIPTION_LIMIT to keep feed payloads small; detail keeps full.
    description: str | None = None
    # In-site author page (ADR-0014 rev.): slug of the video's channel, when
    # attached. Serializers that want the link populate it explicitly; the
    # default None keeps legacy payloads (and cached detail JSON) valid.
    channel_slug: str | None = None
    # Channel cover for the watch-page channel entry card (播放页频道入口);
    # null when the video has no attached channel or the channel has no cover.
    channel_cover_url: str | None = None
    upload_date: str | None = None
    ext_view_count: int | None = None
    ext_like_count: int | None = None
    wpm: float | None = None
    # Populated by the page-batched learning-metadata endpoint; unknown is not zero.
    subtitle_count: int | None = None
    exam_word_count: int | None = None
    sample_text_en: str | None = None
    sample_text_zh: str | None = None
    vocabulary_density: float | None = None
    created_at: str
    # Publish timestamp. Only the rankings card carried it before 批 2; every
    # card does now, because there is one card shape (services/video_card).
    published_at: str | None = None
    # ── Ranking / favorites annotations (only the scope that has them fills
    # these in; null on every other card) ──
    # Ranking metric for the requested scope (weekly deduped plays, favorites,
    # or null for `latest`, which ranks by publish recency and has no count).
    metric: int | None = None
    # First ~60 chars of the viewing user's note on this video (favorites cards).
    note_excerpt: str | None = None
    has_note: bool = False
    favorited_at: str | None = None
    # Fork lineage (Phase 2 standard version): null for originals, UUID of source video for forks
    forked_from: str | None = None
    # Demo/tutorial flag: anonymous viewers may stream the *media file* without
    # a token (api/v1/media.py); the detail payload still follows the login wall.
    is_demo: bool = False
    # 内容三态（需求 §5.1）：local / proxy / offline。前端据此渲染「已下架」态；
    # 默认 local 让历史缓存 JSON 与旧客户端仍可解析。
    storage_mode: str = "local"

    model_config = {"from_attributes": True}

    @field_validator("created_at", "score_updated_at", "upload_date", "published_at", "favorited_at", mode="before")
    @classmethod
    def _serialize_dt_iso(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


class SubtitleResponse(BaseModel):
    id: str
    start_time: float
    end_time: float
    text_en: str
    text_zh: str | None
    sentence_index: int
    grammar_note: str | None
    speaker: str | None
    # Exam-level word annotations: {surface_token: [level keys]} or null.
    word_levels: dict | None = None
    # Word-level timestamps [{word, start, end}, ...] from alignment, or null.
    words: list | None = None

    model_config = {"from_attributes": True}


class VideoDetailResponse(VideoResponse):
    subtitles: list[SubtitleResponse]


class VideoAdminResponse(VideoResponse):
    """Admin-facing video view: exposes featured/notes/error/progress fields
    that the public ``VideoResponse`` intentionally hides."""

    is_featured: bool
    show_on_homepage: bool = False
    admin_notes: str | None = None
    error_message: str | None = None
    processing_progress: int = 0
    # 阶段 5: translation quality flag (None|quality_warning|quality_blocked) for
    # the admin list quality column and quality-filter query.
    quality_flag: str | None = None
    # UGC review audit fields — admin sees why/when a video was rejected.
    rejection_reason: str | None = None
    submitted_at: str | None = None
    reviewed_at: str | None = None
    # Admin-only external metadata extras (阶段 1): full JSON blob with
    # description/tags/categories/caption tracks/channel stats. Public
    # VideoResponse intentionally omits it.
    channel_id: str | None = None
    external_meta: dict | None = None
    # ADR-0014 in-site curated channel (null = unassigned).
    channel_ref: str | None = None
    # Demo/tutorial flag (admin view): anonymous viewers may stream the media
    # file, but the detail payload still follows the login wall.
    is_demo: bool = False

    @field_validator("submitted_at", "reviewed_at", mode="before")
    @classmethod
    def _serialize_dt(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


# DB columns: videos.title / title_zh / topic_tags are varchar(500). Anything
# longer used to reach Postgres and surface as a raw HTTP_500 ("value too long
# for type character varying(500)"); validating here makes it a 422 with the
# offending field named. Kept next to the model so the column and the schema
# limit are one fact.
_VIDEO_TITLE_MAX_LENGTH = 500


class VideoAdminUpdate(BaseModel):
    """Partial update payload for the admin video management panel.

    All fields optional — only supplied fields are written. ``difficulty_level``
    is validated against the CEFR scale used elsewhere in the app.
    """

    title: str | None = Field(None, max_length=_VIDEO_TITLE_MAX_LENGTH)
    # Empty string clears the translation (the admin can remove a bad one and
    # let the next re-translate fill it again).
    title_zh: str | None = Field(None, max_length=_VIDEO_TITLE_MAX_LENGTH)
    difficulty_level: str | None = None
    topic_tags: str | None = Field(None, max_length=_VIDEO_TITLE_MAX_LENGTH)
    is_official: bool | None = None
    is_featured: bool | None = None
    is_published: bool | None = None
    show_on_homepage: bool | None = None
    admin_notes: str | None = None
    # ADR-0014 curated channel. Empty string clears the assignment (the loop
    # below skips None, so a dedicated sentinel keeps clearing expressible).
    channel_ref: str | None = None
    # D0 demo-video toggle (解锁制下示范视频不消耗额度).
    is_demo: bool | None = None

    @field_validator("difficulty_level")
    @classmethod
    def validate_difficulty(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"A1", "A2", "B1", "B2", "C1", "C2"}
        if v.upper() not in allowed:
            raise ValueError("difficulty_level must be one of A1, A2, B1, B2, C1, C2")
        return v.upper()


class SubtitleUpdate(BaseModel):
    """Partial update payload for a single subtitle (admin review/edit).

    All fields optional — only supplied fields are written. Editing ``text_en``
    resets ``word_levels`` to the ECDICT baseline (the inflection index is
    derived from the English text), so manual word-level overrides on that line
    must be redone after an English edit — unless ``preserve_word_levels`` is
    set, in which case existing overrides are kept as-is.
    """

    text_en: str | None = None
    text_zh: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    grammar_note: str | None = None
    speaker: str | None = None
    # When True, editing text_en does NOT reset word_levels to the ECDICT
    # baseline — existing manual overrides are preserved. Default False keeps
    # the original ingest-pipeline behaviour.
    preserve_word_levels: bool = False

    @field_validator("text_en", "text_zh", "grammar_note", "speaker")
    @classmethod
    def strip_and_require_nonempty(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("must not be empty/whitespace")
        return v

    @model_validator(mode="after")
    def validate_timing(self) -> "SubtitleUpdate":
        if self.start_time is not None and self.end_time is not None and self.start_time >= self.end_time:
            raise ValueError("start_time must be less than end_time")
        return self


class SubtitleBatchItem(SubtitleUpdate):
    """One subtitle update within a batch — carries the target subtitle id."""

    id: str


class SubtitleSplit(BaseModel):
    """Payload for splitting one subtitle into two at a given time.

    The original subtitle becomes the ``text_before`` part (end trimmed to
    ``split_time``); a new subtitle is inserted after it for ``text_after``
    (start at ``split_time``, end at the original end). Word-level timestamps,
    when present, are partitioned at ``split_time`` so both parts keep precise
    timing for further split/merge or re-segmentation.
    """

    split_time: float
    text_before: str
    text_after: str

    @field_validator("text_before", "text_after")
    @classmethod
    def strip_and_require_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty/whitespace")
        return v


class SubtitleBatchUpdate(BaseModel):
    """Batch subtitle update payload — applies many edits in one transaction."""

    updates: list[SubtitleBatchItem]


class SubtitleReorderItem(BaseModel):
    """One entry in a reorder request: a subtitle id and its new sentence_index."""

    id: str
    sentence_index: int


class SubtitleReorder(BaseModel):
    """Payload to reorder subtitles within a video (admin canvas editor).

    Accepts a list of ``{id, sentence_index}`` entries. The set of ids must
    match the video's current subtitles exactly, and the new indices must form
    a contiguous ``0..N-1`` sequence (no gaps, no duplicates). Timing is
    re-validated against the new neighbor order - overlaps are rejected.
    """

    items: list[SubtitleReorderItem]


class SubtitleCreate(BaseModel):
    """Payload to create a new subtitle row (admin canvas editor).

    A new row is appended at the end (``sentence_index = current max + 1``).
    The English text may be empty initially (a placeholder the admin fills in);
    ``start_time``/``end_time`` are required and must not overlap existing rows.
    """

    start_time: float
    end_time: float
    text_en: str = ""
    text_zh: str | None = None
    speaker: str | None = None

    @field_validator("text_zh", "speaker")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v

    @field_validator("text_en")
    @classmethod
    def strip_text_en(cls, v: str) -> str:
        # Allow empty (placeholder row) but strip surrounding whitespace.
        return v.strip()

    @model_validator(mode="after")
    def validate_timing(self) -> "SubtitleCreate":
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be less than end_time")
        return self


class WordLevelsUpdate(BaseModel):
    """Manual override of one subtitle's word-level annotations.

    ``word_levels`` maps a lowercase surface token to a list of canonical exam
    level keys (mirrors app.core.exam_levels.EXAM_LEVEL_KEYS). Pass null to
    clear all annotations for the line.

    The rule itself lives in ``app.core.exam_levels.validate_word_levels`` so
    that request validation and the column's normalizer read from one home.
    """

    word_levels: dict[str, list[str]] | None = None

    @field_validator("word_levels")
    @classmethod
    def validate_level_keys(cls, v: dict[str, list[str]] | None) -> dict[str, list[str]] | None:
        validate_word_levels(v)
        return v


class RecomputeWordLevelsRequest(BaseModel):
    """Recompute word_levels from ECDICT for selected subtitles (or all)."""

    subtitle_ids: list[str] | None = None  # None = whole video


# Rejection reasons are read by the video owner and reported in notifications;
# 1000 chars is far more than the admin UI can enter and keeps the reason from
# becoming an unbounded store of pasted text (column itself is TEXT).
_REJECT_REASON_MAX_LENGTH = 1000


class ReviewRejectRequest(BaseModel):
    """Admin rejection payload for a UGC video under review."""

    reason: str = Field(..., max_length=_REJECT_REASON_MAX_LENGTH)

    @field_validator("reason")
    @classmethod
    def require_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("reason must not be empty")
        return v


# Max characters of a pipeline ``error_message`` echoed by the status endpoints.
# The raw text can name absolute paths, yt-dlp/cookies details and third-party
# URLs; the admin status panel only needs the gist. Truncate at the schema
# boundary instead of dropping the value, so failures stay diagnosable.
ERROR_MESSAGE_MAX_LENGTH = 500


class VideoStatusResponse(BaseModel):
    status: str
    video_url_720p: str | None = None
    processing_step: str | None = None
    processing_progress: int | None = None
    error_message: str | None = None
    # Resume hint: number of existing subtitles (non-zero → resume from finalize)
    subtitle_count: int = 0

    @field_validator("error_message", mode="before")
    @classmethod
    def truncate_error_message(cls, v: object) -> object:
        """ADM-18: cap ``error_message`` at ``ERROR_MESSAGE_MAX_LENGTH`` chars.

        Applies to the admin status response (and to the owner-facing status
        response it inherits from) so internal pipeline detail cannot be echoed
        in full. Truncation lives here — at the response boundary — because the
        stored column must keep the full text for triage.
        """
        if isinstance(v, str) and len(v) > ERROR_MESSAGE_MAX_LENGTH:
            return v[:ERROR_MESSAGE_MAX_LENGTH]
        return v


class VideoAdminStatusResponse(VideoStatusResponse):
    """Admin polling response: inherits error_message from VideoStatusResponse
    for immediate display when a video transitions to error status."""

    pass


class WordToken(BaseModel):
    """A single word token with timing from WhisperX forced alignment."""

    word: str
    start: float
    end: float


class TranscriptionSegment(BaseModel):
    """A single subtitle segment returned by the remote GPU transcription worker."""

    start: float
    end: float
    text: str
    # Word-level timestamps from alignment. Optional: absent for legacy workers
    # and the faster-whisper fallback path. When present, persisted to
    # Subtitle.words so the editor/re-segmentation can re-cut precisely.
    words: list[WordToken] | None = None


class TranscriptionCallbackRequest(BaseModel):
    """Inbound callback from the GPU worker delivering transcription results.

    The worker POSTs this to ``/api/v1/internal/transcription/callback``. On
    ``status == "ok"`` the cloud writes the segments as subtitle rows and
    enqueues the tail pipeline; on ``status == "error"`` it marks the video
    failed. Authenticated by a shared ``X-Callback-Secret`` header.
    """

    video_id: str
    status: Literal["ok", "error"]
    segments: list[TranscriptionSegment] | None = None
    error: str | None = None
    # Audio duration (seconds) from ffprobe, used by the cloud to sanity-check
    # the transcription timeline and detect hallucinations.
    audio_duration: float | None = None


class SubtitleSnippet(BaseModel):
    """A matching subtitle snippet returned by subtitle search."""

    id: str
    text_en: str
    start_time: float
    end_time: float


class VideoVocabularyItem(BaseModel):
    """One saved vocabulary row for a single video (BE-07: typed paginated item)."""

    id: str
    word: str
    definition: str | None = None
    translation: str | None = None
    mastery_level: str
    context_sentence: str | None = None
    video_id: str | None = None
    subtitle_id: str | None = None
    review_count: int = 0
    next_review_at: str | None = None
    created_at: str


class VideoLikeToggleResponse(BaseModel):
    liked: bool


class VideoLikeStatusResponse(BaseModel):
    is_liked: bool


class SearchSuggestionsResponse(BaseModel):
    suggestions: list[str]


class HotSearchesResponse(BaseModel):
    hot: list[str]


class PendingCountsResponse(BaseModel):
    pending_processing: int
    pending_review: int
    total: int


class TakedownSuggestionsResponse(BaseModel):
    items: list[VideoResponse]


class QualityReportItem(BaseModel):
    id: str
    stage: str
    passed: bool
    coverage_ratio: float | None = None
    metrics: dict
    issues: list[str]
    segment_count: int | None = None
    created_at: str | None = None


class SubtitleRevisionItem(BaseModel):
    id: str
    subtitle_id: str
    video_id: str
    edited_by: str | None = None
    scope: str | None = None
    before: dict | None = None
    after: dict | None = None
    created_at: str | None = None


class ResegmentResult(BaseModel):
    """Result of a bulk re-segmentation (ADM-01).

    Re-cutting subtitles changes every subtitle id, which used to silently
    delete sentence favorites / revision history and null out vocabulary
    source links through DB cascades. The counts below make the preservation
    auditable: ``*_remapped`` were re-attached to a new segment, ``*_unmatched``
    had no time overlap with any new segment (their rows are kept inside the
    snapshot JSON so a rollback can restore them), ``*_merged`` were duplicates
    collapsed by the ``(user, subtitle)`` uniqueness rule.
    """

    before_count: int
    after_count: int
    translations_cleared: bool = True
    snapshot_id: str
    favorites_total: int = 0
    favorites_remapped: int = 0
    favorites_merged: int = 0
    favorites_unmatched: int = 0
    revisions_total: int = 0
    revisions_preserved: int = 0
    revisions_unmatched: int = 0
    vocabulary_total: int = 0
    vocabulary_relinked: int = 0
    vocabulary_unmatched: int = 0


class ResegmentRollbackResult(BaseModel):
    """Result of rolling back the latest re-segmentation snapshot.

    The current (re-segmented) subtitles are replaced by the snapshotted rows;
    user data attached to them is re-mapped back by time overlap. The
    ``*_restored_from_snapshot`` counters report rows that had been dropped by
    the original re-segmentation and were re-inserted from the snapshot payload.
    """

    restored_count: int
    snapshot_id: str
    favorites_remapped: int = 0
    favorites_unmatched: int = 0
    favorites_restored_from_snapshot: int = 0
    revisions_preserved: int = 0
    revisions_unmatched: int = 0
    revisions_restored_from_snapshot: int = 0
    vocabulary_relinked: int = 0
    vocabulary_unmatched: int = 0
    vocabulary_restored_from_snapshot: int = 0


class SubtitleDeleteResult(BaseModel):
    """Typed response for deleting one subtitle (ADM-01 same-source gap).

    Deleting a subtitle used to cascade-delete its sentence favorites and edit
    history without telling anyone. The endpoint now answers 409 with the
    affected counts unless the caller passes ``?force=true``; this model is the
    successful (forced or impact-free) response.
    """

    deleted_id: str
    remaining_count: int
    favorites_deleted: int = 0
    revisions_deleted: int = 0
    forced: bool = False


class VideoScoreFactors(BaseModel):
    """Per-factor breakdown of the P1 learning score.

    Every factor is nullable: a signal with no data yet is ``None`` (sorts last
    / excluded from the weighted sum), not zero.
    """

    ctr: float | None = None
    retention: float | None = None
    watch_time: float | None = None
    topic_match: float | None = None
    quality: float | None = None
    viral: float | None = None
    freshness: float | None = None
    bonus: float | None = None


class VideoScoreResponse(BaseModel):
    """Typed ``GET /videos/admin/{video_id}/score`` payload (ADM-10).

    The endpoint used to declare ``response_model=dict`` — the values were real
    but OpenAPI degraded to ``object``, so generated clients could not see the
    shape. Field names/values are unchanged from the dict version.
    """

    video_id: str
    total_score: float
    factors: VideoScoreFactors
    computed_at: str | None = None


class RecomputeWordLevelsResponse(BaseModel):
    subtitles_updated: int
    exam_words_found: int


class SubtitleSearchResult(BaseModel):
    """A video with matching subtitle snippets from subtitle search."""

    video: VideoResponse
    matching_subtitles: list[SubtitleSnippet]

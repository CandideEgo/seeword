"""Account data inventory: export gathering + retryable media cleanup (A08/BE-04).

Two jobs live here so the Celery task and the drift tests share one inventory:

``gather_export``
    Reads every user-scoped dataset this product actually stores — profile,
    preferences, vocabulary, learning records/events/profile, favorites, notes,
    sentence favorites, channel subscriptions, likes, vocab sets, study
    sessions, listening attempts, exam attempts + answers, notifications,
    feedback, mastery/milestone history, behavior events, and the metadata of
    videos the user uploaded — plus the on-disk media originals (avatar, uploaded video files, historical shadowing
    audio). Every query is scoped by ``user.id``; child rows are reached only
    through that user's parent ids, so an export can never contain another
    user's rows.

``media_cleanup``
    Account deletion removes DB rows in one transaction and records the paths
    it must delete on disk in ``media_cleanup_tasks`` (A08). The purge task
    drains that queue immediately; anything that fails stays pending with a
    backoff and is retried by the beat task. A failed unlink therefore cannot
    become a silent forever-leak after the user row is gone.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.logging import get_logger

logger = get_logger(__name__)

#: Sections written to the export archive, in reading order. Flat list sections
#: also get a CSV; nested ones (study_sessions, vocab_sets, exam_sessions) only
#: get JSON because a CSV cannot represent their child rows faithfully.
CSV_SECTIONS = frozenset(
    {
        "vocabulary",
        "learning_records",
        "learning_events",
        "favorites",
        "notes",
        "notifications",
        "feedbacks",
        "listening_sessions",
        "video_likes",
        "behavior_events",
    }
)

#: Tables deleted with the account are every table with a ``user_id`` FK to
#: ``users.id`` except the two whose columns were designed to survive:
#: behavior events are anonymized, and videos are handled explicitly (official
#: catalog rows survive).
PURGE_EXCLUDED_TABLES = frozenset({"users", "behavior_events", "videos"})


def scalar(value: Any) -> Any:
    """Convert an ORM column value into something ``json.dumps`` accepts."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): scalar(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [scalar(v) for v in value]
    return str(value)


def row_to_dict(row: Any, *, exclude: frozenset[str] = frozenset()) -> dict[str, Any]:
    """Serialize every column of an ORM row (no relationships, no lazy loads)."""
    return {
        column.key: scalar(getattr(row, column.key)) for column in row.__table__.columns if column.key not in exclude
    }


# ---------------------------------------------------------------------------
# Export gathering
# ---------------------------------------------------------------------------


async def _rows_for_user(db: Any, model: Any, user_id: str, order_by: Any) -> list[dict[str, Any]]:
    rows = (await db.execute(select(model).where(model.user_id == user_id).order_by(order_by))).scalars().all()
    return [row_to_dict(row) for row in rows]


async def gather_user_data(db: Any, user: Any) -> dict[str, Any]:
    """Read every user-scoped dataset. Read-only; all queries filter by user.id."""
    from app.models.behavior import BehaviorEvent
    from app.models.engagement import VideoLike
    from app.models.exam_test import ExamAnswer, ExamSession
    from app.models.favorite import UserFavorite, UserNote
    from app.models.feedback import Feedback
    from app.models.learning import LearningRecord, Vocabulary
    from app.models.learning_plan import LearningEvent, UserLearningProfile
    from app.models.listening import ListeningSession
    from app.models.milestone import MasterySnapshot, UserMilestone
    from app.models.notification import Notification
    from app.models.preferences import UserPreferences
    from app.models.question_exposure import UserExposureMappingState, UserQuestionExposure
    from app.models.study_session import StudySession, StudySessionItem
    from app.models.user_content import ChannelSubscription, SentenceFavorite
    from app.models.vocab_set import VocabSet, VocabSetWord

    sections: list[tuple[str, Any, Any]] = [
        ("vocabulary", Vocabulary, Vocabulary.created_at),
        ("learning_records", LearningRecord, LearningRecord.created_at),
        ("learning_events", LearningEvent, LearningEvent.created_at),
        ("favorites", UserFavorite, UserFavorite.created_at),
        ("notes", UserNote, UserNote.created_at),
        ("sentence_favorites", SentenceFavorite, SentenceFavorite.created_at),
        ("channel_subscriptions", ChannelSubscription, ChannelSubscription.created_at),
        ("video_likes", VideoLike, VideoLike.created_at),
        ("vocab_sets", VocabSet, VocabSet.created_at),
        ("study_sessions", StudySession, StudySession.started_at),
        ("listening_sessions", ListeningSession, ListeningSession.started_at),
        ("exam_sessions", ExamSession, ExamSession.started_at),
        ("question_exposures", UserQuestionExposure, UserQuestionExposure.updated_at),
        ("exposure_mapping_states", UserExposureMappingState, UserExposureMappingState.user_id),
        ("notifications", Notification, Notification.created_at),
        ("feedbacks", Feedback, Feedback.created_at),
        ("mastery_snapshots", MasterySnapshot, MasterySnapshot.snapshot_date),
        ("user_milestones", UserMilestone, UserMilestone.achieved_at),
        ("behavior_events", BehaviorEvent, BehaviorEvent.server_ts),
    ]
    data: dict[str, Any] = {}
    for key, model, order_by in sections:
        data[key] = await _rows_for_user(db, model, user.id, order_by)

    # ---- nested child rows (reached only through this user's parent ids) ----
    set_ids = [row["id"] for row in data["vocab_sets"]]
    if set_ids:
        words = (
            (
                await db.execute(
                    select(VocabSetWord).where(VocabSetWord.set_id.in_(set_ids)).order_by(VocabSetWord.position)
                )
            )
            .scalars()
            .all()
        )
        by_set: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for word in words:
            by_set[word.set_id].append(row_to_dict(word))
        for row in data["vocab_sets"]:
            row["words"] = by_set.get(row["id"], [])

    session_ids = [row["id"] for row in data["study_sessions"]]
    if session_ids:
        items = (
            (
                await db.execute(
                    select(StudySessionItem)
                    .where(StudySessionItem.session_id.in_(session_ids))
                    .order_by(StudySessionItem.sort_order)
                )
            )
            .scalars()
            .all()
        )
        by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            by_session[item.session_id].append(row_to_dict(item))
        for row in data["study_sessions"]:
            row["items"] = by_session.get(row["id"], [])

    exam_ids = [row["id"] for row in data["exam_sessions"]]
    if exam_ids:
        answers = (
            (await db.execute(select(ExamAnswer).where(ExamAnswer.session_id.in_(exam_ids)).order_by(ExamAnswer.id)))
            .scalars()
            .all()
        )
        by_exam: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for answer in answers:
            by_exam[answer.session_id].append(row_to_dict(answer))
        for row in data["exam_sessions"]:
            row["answers"] = by_exam.get(row["id"], [])
            if row["submitted_at"] is None:
                for answer in row["answers"]:
                    answer["question"] = {
                        key: value for key, value in answer["question"].items() if key not in {"answer", "explanation"}
                    }

    # ---- singleton rows ----
    prefs = (await db.execute(select(UserPreferences).where(UserPreferences.user_id == user.id))).scalar_one_or_none()
    data["preferences"] = row_to_dict(prefs) if prefs is not None else {}
    profile = (
        await db.execute(select(UserLearningProfile).where(UserLearningProfile.user_id == user.id))
    ).scalar_one_or_none()
    data["learning_profile"] = row_to_dict(profile) if profile is not None else {}

    data.update(await _gather_teaching_data(db, user.id))
    return data


async def _gather_teaching_data(db: Any, user_id: str) -> dict[str, Any]:
    """Export current user-readable teaching views, never internal content snapshots."""
    from app.services.v2_schema import EXPORT_TABLES, has_tables

    # Export is a legal right, not a V2 feature: on a database whose V2
    # migration never ran there is no teaching data to disclose, and the
    # export must still succeed instead of failing on a missing table.
    if not await has_tables(db, EXPORT_TABLES):
        return {}
    from app.models.teaching import TeachingFeedback, TeachingOperation, TeachingSession, UserQuestionDisclosure
    from app.models.v2_runtime import AgentRun, ExternalConnection, ExternalCredential
    from app.services.external_connection_service import view as connection_view
    from app.services.teaching.principal import Principal
    from app.services.teaching.service import get_session
    from app.services.teaching_runs import summary as run_summary

    sessions = (
        await db.execute(
            select(TeachingSession).where(TeachingSession.user_id == user_id).order_by(TeachingSession.created_at)
        )
    ).scalars()
    projected = [await get_session(db, Principal(user_id), session.id) for session in sessions]
    from app.services.teaching.dialogue import export_all

    conversation_rows, conversations = await export_all(db, Principal(user_id))
    feedbacks = (
        await db.execute(
            select(TeachingFeedback)
            .where(TeachingFeedback.user_id == user_id, TeachingFeedback.expires_at > datetime.now(UTC))
            .order_by(TeachingFeedback.occurred_at)
        )
    ).scalars()
    operations = (
        await db.execute(
            select(TeachingOperation).where(TeachingOperation.user_id == user_id).order_by(TeachingOperation.created_at)
        )
    ).scalars()
    receipts = []
    for row in operations:
        receipts.append(
            {
                "id": row.id,
                "operation_id": row.operation_id,
                "operation_type": row.operation_type,
                "status": row.status,
                "created_at": scalar(row.created_at),
                "result_refs": {
                    key: value
                    for key, value in row.result_refs.items()
                    if key in {"session_id", "item_id", "attempt_id", "feedback_id"} and isinstance(value, str)
                },
            }
        )
    connections = (
        await db.execute(
            select(ExternalConnection)
            .where(ExternalConnection.user_id == user_id)
            .order_by(ExternalConnection.created_at)
        )
    ).scalars()
    connection_summaries = []
    for row in connections:
        credentials = (
            await db.execute(
                select(ExternalCredential)
                .where(ExternalCredential.connection_id == row.id)
                .order_by(ExternalCredential.issued_at)
            )
        ).scalars()
        connection_summaries.append(
            {
                **scalar(connection_view(row)),
                "credentials": [
                    {
                        "id": credential.id,
                        "issued_at": scalar(credential.issued_at),
                        "revoked_at": scalar(credential.revoked_at),
                    }
                    for credential in credentials
                ],
            }
        )
    runs = (
        await db.execute(select(AgentRun).where(AgentRun.user_id == user_id).order_by(AgentRun.created_at))
    ).scalars()
    return {
        "teaching_sessions": projected,
        "tutor_conversations": conversation_rows,
        "teaching_messages": conversations,
        "teaching_attempts": [attempt for session in projected for attempt in session["attempts"]],
        "question_disclosures": await _rows_for_user(
            db, UserQuestionDisclosure, user_id, UserQuestionDisclosure.content_revision_id
        ),
        "teaching_feedbacks": [
            {
                "id": row.id,
                "session_id": row.session_id,
                "content": row.content,
                "verification": row.verification,
                "source_kind": row.source_kind,
                "occurred_at": scalar(row.occurred_at),
                "expires_at": scalar(row.expires_at),
            }
            for row in feedbacks
        ],
        "teaching_operations": receipts,
        "external_connections": connection_summaries,
        "teaching_runs": [
            {**run_summary(row), "created_at": scalar(row.created_at), "finished_at": scalar(row.finished_at)}
            for row in runs
        ],
    }


def profile_dict(user: Any) -> dict[str, Any]:
    """The account row as exported: every user-facing field except the hash."""
    role = getattr(user.role, "value", user.role)
    return {
        "id": user.id,
        "phone": user.phone,
        "name": user.name,
        "level": user.level,
        "role": role,
        "onboarding_completed": user.onboarding_completed,
        "native_language": user.native_language,
        "gender": user.gender,
        "bio": user.bio,
        "timezone": user.timezone,
        "avatar_url": user.avatar_url,
        "created_at": scalar(user.created_at),
        "last_active_at": scalar(user.last_active_at),
        "deletion_requested_at": scalar(user.deletion_requested_at),
        "deletion_scheduled_at": scalar(user.deletion_scheduled_at),
        "deletion_reason": user.deletion_reason,
    }


async def gather_export(db: Any, user: Any) -> tuple[dict[str, Any], list[tuple[Path, str]]]:
    """Everything the export archive needs: section payloads + media originals."""
    from app.models.video import Video

    videos = (
        (await db.execute(select(Video).where(Video.user_id == user.id).order_by(Video.created_at))).scalars().all()
    )
    data = await gather_user_data(db, user)
    data["profile"] = profile_dict(user)
    # Admin-only ops notes are not the uploader's data; everything else about
    # the video (including the frozen published snapshot) is.
    data["videos"] = [row_to_dict(video, exclude=frozenset({"admin_notes"})) for video in videos]
    return data, export_media_entries(user, videos)


#: Archive order. Kept explicit so the README and the ZIP are stable.
EXPORT_ORDER = (
    "profile",
    "preferences",
    "learning_profile",
    "vocabulary",
    "learning_records",
    "learning_events",
    "vocab_sets",
    "study_sessions",
    "favorites",
    "notes",
    "sentence_favorites",
    "channel_subscriptions",
    "video_likes",
    "listening_sessions",
    "exam_sessions",
    "question_exposures",
    "exposure_mapping_states",
    "teaching_sessions",
    "tutor_conversations",
    "teaching_messages",
    "teaching_attempts",
    "question_disclosures",
    "teaching_feedbacks",
    "teaching_operations",
    "external_connections",
    "teaching_runs",
    "videos",
    "notifications",
    "feedbacks",
    "mastery_snapshots",
    "user_milestones",
    "behavior_events",
)


def _media_root() -> Path:
    from app.core.config import get_settings

    return Path(get_settings().local_media_path).resolve()


def resolve_media_url(url: str | None) -> Path | None:
    """Map a stored ``/media/...`` URL to an on-disk path inside the media root."""
    if not url or not url.startswith("/media/"):
        return None
    base = _media_root()
    candidate = (base / url[len("/media/") :]).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _video_media_urls(video: Any) -> list[str | None]:
    return [
        video.thumbnail_url,
        video.video_url_480p,
        video.video_url_720p,
        video.video_url_1080p,
    ]


def export_media_entries(user: Any, videos: list[Any]) -> list[tuple[Path, str]]:
    """On-disk originals to put in the archive, as ``(source, archive path)``."""
    entries: list[tuple[Path, str]] = []
    seen: set[Path] = set()

    def add(path: Path | None, arcname: str) -> None:
        if path is None or path in seen or not path.is_file():
            return
        seen.add(path)
        entries.append((path, arcname))

    add(resolve_media_url(user.avatar_url), f"media/avatar/{Path(user.avatar_url or '').name}")
    for video in videos:
        for url in _video_media_urls(video):
            path = resolve_media_url(url)
            if path is not None:
                add(path, f"media/videos/{path.name}")
        raw = _media_root() / f"{video.id}_raw.mp4"
        add(raw, f"media/videos/{raw.name}")

    shadow_root = _media_root() / "shadowing" / user.id
    if shadow_root.is_dir():
        for path in sorted(shadow_root.rglob("*")):
            if path.is_file():
                entries.append((path, f"media/shadowing/{path.relative_to(shadow_root).as_posix()}"))
    return entries


# ---------------------------------------------------------------------------
# Retryable media cleanup
# ---------------------------------------------------------------------------


def _relative_media_path(path: Path) -> str | None:
    root = _media_root()
    try:
        return path.resolve().relative_to(root).as_posix()
    except (ValueError, OSError):
        return None


def cleanup_paths(user: Any, videos: list[Any], export_file_paths: list[str]) -> tuple[list[str], list[str]]:
    """Relative paths the purge must delete: ``(files, directories)``."""
    files: set[str] = set()
    dirs: set[str] = set()

    def add(url: str | None) -> None:
        path = resolve_media_url(url)
        if path is not None:
            rel = _relative_media_path(path)
            if rel:
                files.add(rel)

    add(user.avatar_url)
    for video in videos:
        # Official videos are platform content: the row is kept and its media
        # must not be removed with the admin account that uploaded it.
        if video.is_official:
            continue
        for url in _video_media_urls(video):
            add(url)
        raw = _media_root() / f"{video.id}_raw.mp4"
        if raw.is_file():
            rel = _relative_media_path(raw)
            if rel:
                files.add(rel)

    for rel in export_file_paths:
        if rel:
            files.add(Path(rel).as_posix())
    dirs.add(f"exports/{user.id}")
    if (_media_root() / "shadowing" / user.id).exists():
        dirs.add(f"shadowing/{user.id}")
    return sorted(files), sorted(dirs)


async def enqueue_media_cleanup(db: Any, user_id: str, files: list[str], dirs: list[str]) -> int:
    """Record paths inside the caller's transaction (caller commits with the purge)."""
    from app.models.media_cleanup import MediaCleanupTask

    if not files and not dirs:
        return 0
    wanted = [(path, "file") for path in files] + [(path, "dir") for path in dirs]
    existing = set(
        (
            await db.execute(
                select(MediaCleanupTask.path).where(
                    MediaCleanupTask.path.in_([path for path, _ in wanted]),
                    MediaCleanupTask.status == "pending",
                )
            )
        )
        .scalars()
        .all()
    )
    created = 0
    for path, kind in wanted:
        if path in existing:
            continue
        db.add(MediaCleanupTask(user_id=user_id, path=path, kind=kind))
        created += 1
    return created


def _remove_path(relative: str, kind: str) -> None:
    root = _media_root()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:  # never touch anything outside the media root
        raise ValueError(f"path escapes the media root: {relative}") from exc
    if kind == "dir":
        import shutil

        if target.is_dir():
            shutil.rmtree(target)
        return
    target.unlink(missing_ok=True)


async def process_media_cleanup(db: Any, *, limit: int = 200, now: datetime | None = None) -> dict[str, int]:
    """Drain due cleanup rows. Failures stay pending with a capped backoff."""
    from sqlalchemy import or_

    from app.models.media_cleanup import MediaCleanupTask

    now_utc = now or datetime.now(UTC)
    rows = (
        (
            await db.execute(
                select(MediaCleanupTask)
                .where(
                    MediaCleanupTask.status == "pending",
                    or_(
                        MediaCleanupTask.next_attempt_at.is_(None),
                        MediaCleanupTask.next_attempt_at <= now_utc,
                    ),
                )
                .order_by(MediaCleanupTask.created_at)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    done = 0
    failed = 0
    for row in rows:
        try:
            _remove_path(row.path, row.kind)
        except Exception as exc:
            row.attempts = (row.attempts or 0) + 1
            row.last_error = (str(exc) or exc.__class__.__name__)[:1000]
            backoff = min(3600, 30 * (2 ** min(row.attempts, 7)))
            row.next_attempt_at = now_utc + timedelta(seconds=backoff)
            row.updated_at = now_utc
            failed += 1
            logger.warning("media_cleanup_failed", path=row.path, attempts=row.attempts, exc_info=True)
        else:
            row.status = "done"
            row.last_error = None
            row.next_attempt_at = None
            row.updated_at = now_utc
            done += 1
        await db.commit()
    return {"processed": len(rows), "done": done, "failed": failed}


async def prune_media_cleanup(db: Any, *, older_than_days: int = 30, now: datetime | None = None) -> int:
    from sqlalchemy import delete

    from app.models.media_cleanup import MediaCleanupTask

    cutoff = (now or datetime.now(UTC)) - timedelta(days=older_than_days)
    result = await db.execute(
        delete(MediaCleanupTask).where(
            MediaCleanupTask.status == "done",
            MediaCleanupTask.updated_at < cutoff,
        )
    )
    await db.commit()
    return int(getattr(result, "rowcount", 0) or 0)

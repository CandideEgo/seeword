"""Per-video favorites & notes — account-scoped (replaces watch-page localStorage).

Routes are video-scoped (prefix ``/videos``) so they read naturally as
``/videos/{video_id}/favorite`` etc. Authenticated only.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.models.favorite import UserFavorite, UserNote
from app.models.user import User
from app.models.video import Video
from app.services.video_cache import invalidate_favorite_caches

router = APIRouter(prefix="/videos", tags=["favorites"])


class NoteUpdate(BaseModel):
    content: str = Field(default="", max_length=10000)


class FavoriteStatus(BaseModel):
    is_favorited: bool


class NoteResponse(BaseModel):
    content: str


class WatchMeta(BaseModel):
    """Combined favorite + note state for the watch page's initial load."""

    is_favorited: bool
    note: str


async def _get_owned_video_or_404(db: AsyncSession, video_id: str, *, for_update: bool = False) -> Video:
    stmt = select(Video).where(Video.id == video_id)
    if for_update:
        stmt = stmt.with_for_update()
    video = (await db.execute(stmt)).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/watch-meta", response_model=WatchMeta)
@rate_limit("30/minute")
async def get_watch_meta(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's favorite status + note for a video in one call."""
    # One round trip answers all three questions: does the video exist, is it
    # favorited, and what is the note. Both joins are on the unique
    # (user_id, video_id) pairs, so this stays a single row per video.
    row = (
        await db.execute(
            select(UserFavorite.id, UserNote.content)
            .select_from(Video)
            .outerjoin(
                UserFavorite,
                and_(UserFavorite.video_id == Video.id, UserFavorite.user_id == current_user.id),
            )
            .outerjoin(
                UserNote,
                and_(UserNote.video_id == Video.id, UserNote.user_id == current_user.id),
            )
            .where(Video.id == video_id)
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Video not found")
    favorite_id, note_content = row
    return WatchMeta(is_favorited=favorite_id is not None, note=note_content or "")


@router.post("/{video_id}/favorite", response_model=FavoriteStatus)
@rate_limit("20/minute")
async def add_favorite(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a video (idempotent). Increments favorite_count on the video.

    Race-safe: locks the video row first, then checks for an existing
    favorite.  If two concurrent requests both pass the check, the
    ``uq_user_favorite_user_video`` constraint rejects the duplicate INSERT
    and we treat it as already-favorited (no counter over-increment).
    """
    # Lock the video row FIRST to serialize concurrent counter updates.
    video = (await db.execute(select(Video).where(Video.id == video_id).with_for_update())).scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    existing = (
        await db.execute(
            select(UserFavorite).where(
                UserFavorite.user_id == current_user.id,
                UserFavorite.video_id == video_id,
            )
        )
    ).scalar_one_or_none()
    if not existing:
        db.add(UserFavorite(user_id=current_user.id, video_id=video_id))
        video.favorite_count = (video.favorite_count or 0) + 1
        # Auto-feature check
        from app.services.video_like_service import FEATURE_THRESHOLD

        if video.like_count >= FEATURE_THRESHOLD or video.favorite_count >= FEATURE_THRESHOLD:
            video.is_featured = True
        try:
            await db.commit()
            await invalidate_favorite_caches(video_id)
        except IntegrityError:
            # Duplicate favorite from a race — treat as already favorited
            await db.rollback()
    return FavoriteStatus(is_favorited=True)


@router.delete("/{video_id}/favorite", response_model=FavoriteStatus)
@rate_limit("20/minute")
async def remove_favorite(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a video bookmark (idempotent). Decrements favorite_count atomically.

    Race-safe: locks the video row first, then fetches the existing
    favorite with ``with_for_update`` so that two concurrent removes
    cannot both see the same row and double-decrement the counter.
    """
    # Lock the video row FIRST to serialize concurrent counter updates.
    video = (await db.execute(select(Video).where(Video.id == video_id).with_for_update())).scalar_one_or_none()

    existing = (
        await db.execute(
            select(UserFavorite)
            .where(
                UserFavorite.user_id == current_user.id,
                UserFavorite.video_id == video_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if existing:
        if video:
            video.favorite_count = max(0, video.favorite_count - 1)
        await db.delete(existing)
        await db.commit()
        await invalidate_favorite_caches(video_id)
    return FavoriteStatus(is_favorited=False)


@router.get("/{video_id}/note", response_model=NoteResponse)
@rate_limit("30/minute")
async def get_note(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_video_or_404(db, video_id)
    note = (
        await db.execute(
            select(UserNote).where(
                UserNote.user_id == current_user.id,
                UserNote.video_id == video_id,
            )
        )
    ).scalar_one_or_none()
    return NoteResponse(content=note.content if note else "")


@router.put("/{video_id}/note", response_model=NoteResponse)
@rate_limit("10/minute")
async def upsert_note(
    request: Request,
    video_id: str,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update the user's note for a video (upsert).

    Race-safe: locks the video row first (mirroring ``add_favorite``), which
    serializes concurrent upserts for the same video. Without it two parallel
    PUTs both see "no note" and the second INSERT trips
    ``uq_user_note_user_video``, failing the request with an uncaught
    ``IntegrityError`` (500) instead of saving the note.
    """
    # Lock the video row FIRST — the note row cannot serve as the mutex here,
    # because on the insert path it does not exist yet.
    await _get_owned_video_or_404(db, video_id, for_update=True)
    note = (
        await db.execute(
            select(UserNote).where(
                UserNote.user_id == current_user.id,
                UserNote.video_id == video_id,
            )
        )
    ).scalar_one_or_none()
    if not note:
        note = UserNote(user_id=current_user.id, video_id=video_id, content=data.content)
        db.add(note)
    else:
        note.content = data.content
    await db.commit()
    return NoteResponse(content=note.content)


@router.delete("/{video_id}/note", response_model=NoteResponse)
@rate_limit("20/minute")
async def delete_note(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the user's note for a video (idempotent).

    Race-safe: locks the video row first — the same mutex ``upsert_note``
    takes — then reads the note with ``with_for_update``. Together they close
    both ways a concurrent note writer used to break this endpoint: two
    parallel DELETEs both load the note, so the slower one deletes a row that
    is already gone; a parallel PUT is otherwise free to UPDATE the note
    between our read and our delete, and either loses that write silently or
    fails its own UPDATE with ``StaleDataError`` (500).

    No video-existence check: an unknown video is not an error for an
    idempotent delete, and it has no row to lock and no note to remove.
    """
    # Take the video row lock first so a concurrent PUT (which holds it for the
    # whole of ``upsert_note``) cannot interleave with this read-then-delete.
    await db.execute(select(Video).where(Video.id == video_id).with_for_update())
    note = (
        await db.execute(
            select(UserNote)
            .where(
                UserNote.user_id == current_user.id,
                UserNote.video_id == video_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if note:
        await db.delete(note)
        await db.commit()
    return NoteResponse(content="")

"""Video access control — domain logic (not FastAPI dependencies).

Consolidates the "who can access what" rules and the UGC snapshot predicate so
every entry point answers them the same way. These are pure domain functions
with no HTTP/FastAPI dependency, so route handlers and services import them
directly from here.

Callers: app/api/v1/media.py, app/api/v1/notes.py, app/services/video_service.py,
app/services/video_card.py, app/services/subtitle_context.py and
app/services/discovery_service.py.
"""

from app.models.user import RoleType, User
from app.models.video import Video, VideoReviewStatus


def is_video_owner(video: Video, current_user: User | None) -> bool:
    """True if ``current_user`` owns ``video`` (UGC ownership check)."""
    return current_user is not None and video.user_id == current_user.id


def check_video_access(video: Video, current_user: User | None) -> bool:
    """Check whether a user can access a video.

    Access rules:
    - Official videos are public (anyone can access).
    - User-uploaded (UGC) videos are public once ``review_status == published``.
    - A UGC video under re-review (``pending_review``/``rejected``) stays public
      if it has a ``published_snapshot`` (the public keeps watching the last
      approved version); otherwise it is private.
    - The owner can always access their own video (incl. drafts).

    Returns True if access is allowed, False otherwise.
    """
    return check_video_access_by_owner(video, current_user.id if current_user is not None else None)


def check_video_access_by_owner(video: Video, viewer_id: str | None) -> bool:
    """``check_video_access`` variant taking the viewer's user id directly.

    Used by media serving, which resolves viewers from JWTs (?token=/Bearer)
    without loading a User row — the common public path must not pay an extra
    DB query per media request.
    """
    if video.is_official:
        return True
    if viewer_id is not None and video.user_id == viewer_id:
        return True
    review_status = getattr(video, "review_status", None)
    if review_status == "published":
        return True
    # Under re-review with a frozen approved version: still publicly viewable.
    if review_status in ("pending_review", "rejected") and getattr(video, "published_snapshot", None):
        return True
    return False


def is_admin(viewer: User | None) -> bool:
    """True if ``viewer`` is an admin (role read from the loaded User row).

    The media publish-state gate uses this to let admins preview draft /
    unpublished media. The role is deliberately read from the DB-backed User
    row (not the JWT), matching ``get_admin_user`` in the API layer.
    """
    return viewer is not None and viewer.role == RoleType.admin


def should_use_snapshot(video: Video, current_user: User | None) -> bool:
    """A non-owner viewing a UGC video under re-review sees the frozen approved
    snapshot instead of the owner's live draft.

    This predicate must stay consistent with ``check_video_access``: a non-owner
    can *access* such a video (because of the snapshot), and when they do they
    must *see* the snapshot (not the live draft).  Centralising both here is the
    single seam where the two halves are guaranteed not to drift.

    Returns True iff all of:
      - the video is UGC (not official)
      - the viewer is not the owner
      - review_status is pending_review or rejected (re-review in progress)
      - a published_snapshot exists (a previously-approved version to show)
    """
    return (
        not video.is_official
        and not is_video_owner(video, current_user)
        and video.review_status in (VideoReviewStatus.pending_review.value, VideoReviewStatus.rejected.value)
        and video.published_snapshot is not None
    )

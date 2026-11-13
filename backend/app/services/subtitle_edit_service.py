"""Subtitle editing service — CRUD for subtitle rows and word-level annotations."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import commit_refresh
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.subtitle_revision import AUDITED_FIELDS, SubtitleRevision
from app.schemas.pagination import paginated
from app.schemas.video import (
    SubtitleBatchUpdate,
    SubtitleResponse,
    SubtitleUpdate,
    WordLevelsUpdate,
)
from app.services.subtitle_resegment_rules import (
    RemapPlan as _RemapPlan,
)
from app.services.subtitle_resegment_rules import (
    UserDataCapture as _UserDataCapture,
)
from app.services.subtitle_resegment_rules import (
    build_remap_plan as _build_remap_plan,
)
from app.services.subtitle_resegment_rules import (
    map_interval_to_segment as _map_interval_to_segment,
)
from app.services.subtitle_resegment_rules import (
    parse_snapshot_dt as _parse_snapshot_dt,
)
from app.services.subtitle_resegment_rules import (
    parse_snapshot_payload as _parse_snapshot_payload,
)
from app.services.subtitle_resegment_rules import (
    remap_counts as _remap_counts,
)
from app.services.subtitle_resegment_rules import (
    resegment_segments as _resegment_segments,
)
from app.services.subtitle_resegment_rules import (
    snapshot_payload as _snapshot_payload,
)
from app.services.subtitle_resegment_rules import (
    subtitle_snapshot_dict as _subtitle_snapshot_dict,
)
from app.services.video_cache import invalidate_video_detail_cache


async def _determine_edit_scope(db: AsyncSession, video_id: str) -> str:
    """'standard' if this video IS the canonical standard for its URL, else 'fork'.

    Drives the ``scope`` column on SubtitleRevision (Grilling 决议 1/5): edits
    to a standard body are shared (affect future forks), edits to a fork are
    private to that user's copy.
    """
    from app.models.video_standard import VideoStandard

    result = await db.execute(select(VideoStandard).where(VideoStandard.canonical_video_id == video_id))
    return "standard" if result.scalar_one_or_none() is not None else "fork"


def _snapshot(subtitle) -> dict:
    """Capture the audited fields of a subtitle as a dict (before or after state)."""
    return {f: getattr(subtitle, f) for f in AUDITED_FIELDS}


def _diff(before: dict, after: dict) -> tuple[dict, dict] | None:
    """Return (before_delta, after_delta) of changed fields, or None if unchanged."""
    changed_before = {k: v for k, v in before.items() if v != after[k]}
    if not changed_before:
        return None
    changed_after = {k: after[k] for k in changed_before}
    return changed_before, changed_after


async def _write_revision(
    db: AsyncSession,
    subtitle,
    before_snap: dict,
    after_snap: dict,
    *,
    edited_by: str | None,
    scope: str,
) -> None:
    """Write a SubtitleRevision row if the edit actually changed anything."""
    diff = _diff(before_snap, after_snap)
    if diff is None:
        return
    before_delta, after_delta = diff
    db.add(
        SubtitleRevision(
            subtitle_id=subtitle.id,
            video_id=subtitle.video_id,
            edited_by=edited_by,
            scope=scope,
            before=before_delta,
            after=after_delta,
        )
    )


async def _validate_timing(db: AsyncSession, video_id: str, subtitle) -> None:
    """Validate a subtitle's timing after an edit has been applied in memory.

    Checks ``start_time < end_time`` and that the interval does not overlap its
    immediate neighbors (ordered by ``sentence_index``). Gaps and touching
    boundaries are allowed; overlaps are rejected. Raises ``Invalid`` — route
    handlers map that to HTTP 400.
    """
    from app.models.subtitle import Subtitle

    if subtitle.start_time >= subtitle.end_time:
        raise BadRequestError("start_time must be less than end_time")

    prev_q = (
        select(Subtitle)
        .where(
            Subtitle.video_id == video_id,
            Subtitle.id != subtitle.id,
            Subtitle.sentence_index < subtitle.sentence_index,
        )
        .order_by(Subtitle.sentence_index.desc())
        .limit(1)
    )
    next_q = (
        select(Subtitle)
        .where(
            Subtitle.video_id == video_id,
            Subtitle.id != subtitle.id,
            Subtitle.sentence_index > subtitle.sentence_index,
        )
        .order_by(Subtitle.sentence_index.asc())
        .limit(1)
    )
    prev = (await db.execute(prev_q)).scalar_one_or_none()
    nxt = (await db.execute(next_q)).scalar_one_or_none()
    if prev is not None and subtitle.start_time < prev.end_time:
        raise BadRequestError(f"start_time {subtitle.start_time} overlaps previous subtitle (ends at {prev.end_time})")
    if nxt is not None and subtitle.end_time > nxt.start_time:
        raise BadRequestError(f"end_time {subtitle.end_time} overlaps next subtitle (starts at {nxt.start_time})")


async def update_subtitle(
    db: AsyncSession,
    video_id: str,
    subtitle_id: str,
    payload: SubtitleUpdate,
    *,
    edited_by: str | None = None,
) -> SubtitleResponse:
    """Apply a partial admin edit to one subtitle.

    Editing ``text_en`` resets ``word_levels`` to the ECDICT baseline (the
    inflection index is derived from the English text), mirroring the ingest
    pipeline.  Pass ``preserve_word_levels=True`` to keep existing overrides.

    Phase 3: writes a ``SubtitleRevision`` audit row (before/after delta +
    ``scope`` fork|standard) capturing the edit, for history/rollback.
    ``edited_by`` should be the acting user's id.
    """
    from app.models.subtitle import Subtitle
    from app.services.ecdict import annotate_text

    result = await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id))
    subtitle = result.scalar_one_or_none()
    if subtitle is None:
        raise NotFoundError("Subtitle not found")
    if subtitle.video_id != video_id:
        raise BadRequestError("Subtitle does not belong to this video")

    before_snap = _snapshot(subtitle)

    text_en_changed = payload.text_en is not None and payload.text_en != subtitle.text_en

    for field in ("text_en", "text_zh", "start_time", "end_time", "grammar_note", "speaker"):
        value = getattr(payload, field)
        if value is not None:
            setattr(subtitle, field, value)

    await _validate_timing(db, video_id, subtitle)

    if text_en_changed:
        subtitle.words = None
        if not payload.preserve_word_levels:
            # Re-derive word_levels from the new English text — same primitive the
            # finalize pipeline and backfill script use. This overwrites any manual
            # overrides on this line; UI should warn before editing text_en. Pass
            # ``preserve_word_levels=True`` to keep existing overrides.
            levels = annotate_text(subtitle.text_en)
            subtitle.word_levels = levels or None

    after_snap = _snapshot(subtitle)

    scope = await _determine_edit_scope(db, video_id)
    await _write_revision(db, subtitle, before_snap, after_snap, edited_by=edited_by, scope=scope)

    await commit_refresh(db, subtitle)
    await invalidate_video_detail_cache(video_id)
    return SubtitleResponse.model_validate(subtitle)


async def update_subtitles_batch(
    db: AsyncSession,
    video_id: str,
    payload: SubtitleBatchUpdate,
    *,
    edited_by: str | None = None,
) -> list[SubtitleResponse]:
    """Apply many subtitle edits in one transaction. All ids must belong to video_id.

    Phase 3: writes a ``SubtitleRevision`` per changed subtitle (scope resolved
    once for the whole batch — same video).
    """
    from app.models.subtitle import Subtitle
    from app.services.ecdict import annotate_text

    if not payload.updates:
        return []

    ids = [item.id for item in payload.updates]
    result = await db.execute(select(Subtitle).where(Subtitle.id.in_(ids)))
    subtitles_by_id = {s.id: s for s in result.scalars().all()}

    # Validate every target up front so we don't partially apply.
    for item in payload.updates:
        sub = subtitles_by_id.get(item.id)
        if sub is None:
            raise NotFoundError(f"Subtitle {item.id} not found")
        if sub.video_id != video_id:
            raise BadRequestError(f"Subtitle {item.id} does not belong to this video")

    scope = await _determine_edit_scope(db, video_id)
    pending: list[tuple] = []
    for item in payload.updates:
        sub = subtitles_by_id[item.id]
        before_snap = _snapshot(sub)
        text_en_changed = item.text_en is not None and item.text_en != sub.text_en
        for field in ("text_en", "text_zh", "start_time", "end_time", "grammar_note", "speaker"):
            value = getattr(item, field)
            if value is not None:
                setattr(sub, field, value)
        if text_en_changed:
            sub.words = None
            if not item.preserve_word_levels:
                levels = annotate_text(sub.text_en)
                sub.word_levels = levels or None
        pending.append((sub, before_snap))

    # Apply the whole batch before validating: validating inside the loop would
    # check each edit against neighbors that later items have not updated yet,
    # so acceptance depended on payload order.
    await db.flush()
    for sub, _ in pending:
        await _validate_timing(db, video_id, sub)

    updated: list[SubtitleResponse] = []
    for sub, before_snap in pending:
        after_snap = _snapshot(sub)
        await _write_revision(db, sub, before_snap, after_snap, edited_by=edited_by, scope=scope)
        updated.append(SubtitleResponse.model_validate(sub))

    await db.commit()
    for sub in subtitles_by_id.values():
        if sub.id in ids:
            await db.refresh(sub)
    await invalidate_video_detail_cache(video_id)

    # Return in the order requested, refreshed.
    refreshed = {s.id: s for s in subtitles_by_id.values()}
    return [SubtitleResponse.model_validate(refreshed[item.id]) for item in payload.updates]


async def update_word_levels(
    db: AsyncSession,
    video_id: str,
    subtitle_id: str,
    payload: WordLevelsUpdate,
) -> SubtitleResponse:
    """Manually override one subtitle's word_levels (admin review)."""
    from app.models.subtitle import Subtitle

    result = await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id))
    subtitle = result.scalar_one_or_none()
    if subtitle is None:
        raise NotFoundError("Subtitle not found")
    if subtitle.video_id != video_id:
        raise BadRequestError("Subtitle does not belong to this video")

    subtitle.word_levels = payload.word_levels  # None clears all annotations
    await commit_refresh(db, subtitle)
    await invalidate_video_detail_cache(video_id)
    return SubtitleResponse.model_validate(subtitle)


async def reorder_subtitles(
    db: AsyncSession,
    video_id: str,
    payload,  # SubtitleReorder
    *,
    edited_by: str | None = None,
) -> list[SubtitleResponse]:
    """Reassign ``sentence_index`` for every subtitle in one transaction.

    The payload must include exactly one entry per current subtitle, and the
    new indices must form a contiguous ``0..N-1`` sequence. After reassigning,
    timing is re-validated against the new neighbor order (``_validate_timing``)
    - reordering without adjusting times can produce overlaps, which are
    rejected. ``sentence_index`` is not an audited field, so no
    ``SubtitleRevision`` rows are written (consistent with the audit system
    tracking content, not ordering). Returns all subtitles in new index order.
    """
    from app.models.subtitle import Subtitle

    result = await db.execute(select(Subtitle).where(Subtitle.video_id == video_id))
    subs_by_id = {s.id: s for s in result.scalars().all()}
    if not subs_by_id:
        raise BadRequestError("视频没有字幕，无法重排")

    items = payload.items
    if len(items) != len(subs_by_id):
        raise BadRequestError(f"reorder must include all {len(subs_by_id)} subtitles, got {len(items)}")

    seen_ids: set[str] = set()
    seen_indices: set[int] = set()
    for item in items:
        if item.id not in subs_by_id:
            raise BadRequestError(f"Subtitle {item.id} does not belong to this video")
        if item.id in seen_ids:
            raise BadRequestError(f"Duplicate subtitle id in reorder: {item.id}")
        if item.sentence_index in seen_indices:
            raise BadRequestError(f"Duplicate sentence_index in reorder: {item.sentence_index}")
        if item.sentence_index < 0 or item.sentence_index >= len(subs_by_id):
            raise BadRequestError(f"sentence_index {item.sentence_index} out of range (0..{len(subs_by_id) - 1})")
        seen_ids.add(item.id)
        seen_indices.add(item.sentence_index)

    for item in items:
        subs_by_id[item.id].sentence_index = item.sentence_index

    # Re-validate timing against the new neighbor order. Reordering can make a
    # subtitle overlap its new neighbors (times weren't moved), which we reject.
    for sub in subs_by_id.values():
        await _validate_timing(db, video_id, sub)

    await db.commit()
    for sub in subs_by_id.values():
        await db.refresh(sub)
    await invalidate_video_detail_cache(video_id)

    ordered = sorted(subs_by_id.values(), key=lambda s: s.sentence_index)
    return [SubtitleResponse.model_validate(s) for s in ordered]


async def lock_video_row(db: AsyncSession, video_id: str) -> None:
    """Serialize subtitle-index allocation by locking the owning video row.

    ``create_subtitle`` derives ``sentence_index`` from ``max(index) + 1``; two
    concurrent appends would read the same max and insert two rows with the
    same index (``sentence_index`` has no unique constraint, so nothing else
    stops it — only ordering in the editor breaks). ``SELECT ... FOR UPDATE``
    on the parent video row makes the read-allocate-insert sequence atomic in
    Postgres; SQLite (the test DB) ignores the clause, which is why the lock is
    also asserted structurally in the tests rather than by racing two writers.
    """
    from app.models.video import Video

    await db.execute(select(Video.id).where(Video.id == video_id).with_for_update())


async def create_subtitle(
    db: AsyncSession,
    video_id: str,
    payload,  # SubtitleCreate
    *,
    edited_by: str | None = None,
) -> SubtitleResponse:
    """Append a new subtitle row at the end of the video.

    ``sentence_index`` is set to ``current max + 1`` (or 0 for the first row).
    The English text may be empty (a placeholder the admin fills in); when
    present, word_levels are derived from ECDICT. Timing is validated against
    existing rows (non-overlap) before commit.

    The index allocation is serialized with ``lock_video_row`` (ADM-14) so
    concurrent appends cannot produce duplicate indices.
    """
    from app.models.subtitle import Subtitle
    from app.services.ecdict import annotate_text

    await lock_video_row(db, video_id)

    last_q = select(Subtitle).where(Subtitle.video_id == video_id).order_by(Subtitle.sentence_index.desc()).limit(1)
    last = (await db.execute(last_q)).scalar_one_or_none()
    new_index = (last.sentence_index + 1) if last else 0

    new_sub = Subtitle(
        video_id=video_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        text_en=payload.text_en,
        text_zh=payload.text_zh,
        sentence_index=new_index,
        speaker=payload.speaker,
    )
    if payload.text_en:
        levels = annotate_text(payload.text_en)
        new_sub.word_levels = levels or None

    # Validate against existing rows before persisting (the new row isn't in the
    # DB yet, so _validate_timing checks it as the tail neighbor).
    await _validate_timing(db, video_id, new_sub)

    db.add(new_sub)
    await commit_refresh(db, new_sub)
    await invalidate_video_detail_cache(video_id)
    return SubtitleResponse.model_validate(new_sub)


async def delete_subtitle(
    db: AsyncSession,
    video_id: str,
    subtitle_id: str,
    *,
    edited_by: str | None = None,
    force: bool = False,
) -> dict:
    """Delete one subtitle and close the gap in ``sentence_index``.

    Subtitles after the deleted row shift down by one so indices stay
    contiguous. Deleting never creates overlaps (gaps are allowed), so no
    timing re-validation is needed.

    ADM-01: the same DB cascades that made bulk re-segmentation lossy apply
    here too —
    ``sentence_favorites`` / ``subtitle_revisions`` cascade-delete and
    ``vocabulary.subtitle_id`` is set null. A plain delete therefore answers
    409 with the affected counts; the caller must pass ``force=True`` to accept
    losing them. The cascades are executed explicitly (not left to the DB) so
    the behaviour is identical on Postgres and the SQLite test DB.

    Returns ``{deleted_id, remaining_count, favorites_deleted, revisions_deleted,
    forced}``.
    """
    from app.models.learning import Vocabulary
    from app.models.subtitle import Subtitle
    from app.models.user_content import SentenceFavorite

    result = await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id))
    sub = result.scalar_one_or_none()
    if sub is None:
        raise NotFoundError("Subtitle not found")
    if sub.video_id != video_id:
        raise BadRequestError("Subtitle does not belong to this video")

    favorites = (
        await db.scalar(
            select(func.count()).select_from(SentenceFavorite).where(SentenceFavorite.subtitle_id == subtitle_id)
        )
    ) or 0
    revisions = (
        await db.scalar(
            select(func.count()).select_from(SubtitleRevision).where(SubtitleRevision.subtitle_id == subtitle_id)
        )
    ) or 0

    if (favorites or revisions) and not force:
        raise ConflictError(
            f"删除该字幕会一并清除 {favorites} 条用户原句收藏、{revisions} 条编辑历史；"
            f"确认无影响后请带 ?force=true 重试",
            detail={
                "subtitle_id": subtitle_id,
                "affected_favorites": favorites,
                "affected_revisions": revisions,
            },
        )

    if favorites:
        await db.execute(delete(SentenceFavorite).where(SentenceFavorite.subtitle_id == subtitle_id))
    if revisions:
        await db.execute(delete(SubtitleRevision).where(SubtitleRevision.subtitle_id == subtitle_id))
    # Mirror the DB's ON DELETE SET NULL so the vocabulary row never keeps a
    # dangling subtitle id on a backend that does not enforce FKs (SQLite).
    await db.execute(update(Vocabulary).where(Vocabulary.subtitle_id == subtitle_id).values(subtitle_id=None))

    deleted_index = sub.sentence_index
    await db.delete(sub)
    await db.flush()  # persist the delete before the index shift

    await db.execute(
        update(Subtitle)
        .where(
            Subtitle.video_id == video_id,
            Subtitle.sentence_index > deleted_index,
        )
        .values(sentence_index=Subtitle.sentence_index - 1)
    )

    await db.commit()
    await invalidate_video_detail_cache(video_id)

    count_q = select(Subtitle).where(Subtitle.video_id == video_id)
    remaining = len((await db.execute(count_q)).scalars().all())
    return {
        "deleted_id": subtitle_id,
        "remaining_count": remaining,
        "favorites_deleted": favorites,
        "revisions_deleted": revisions,
        "forced": force,
    }


async def split_subtitle(
    db: AsyncSession,
    video_id: str,
    subtitle_id: str,
    payload,  # SubtitleSplit
    *,
    edited_by: str | None = None,
) -> list:
    """Split one subtitle into two at ``payload.split_time``.

    The original subtitle becomes the ``text_before`` part (end trimmed to
    ``split_time``); a new subtitle is inserted after it for ``text_after``
    (start at ``split_time``, end at the original end). Word-level timestamps
    are partitioned at ``split_time`` so both parts keep precise timing.
    ``sentence_index`` of subsequent subtitles is shifted up by one.

    Returns ``[before_part, after_part]`` (both refreshed). A SubtitleRevision
    is written for the original subtitle's field changes; the new subtitle is
    audited implicitly via its existence (merge reverses a split).
    """
    from sqlalchemy import update

    from app.models.subtitle import Subtitle
    from app.services.ecdict import annotate_text

    result = await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id))
    subtitle = result.scalar_one_or_none()
    if subtitle is None:
        raise NotFoundError("Subtitle not found")
    if subtitle.video_id != video_id:
        raise BadRequestError("Subtitle does not belong to this video")
    if not (subtitle.start_time < payload.split_time < subtitle.end_time):
        raise BadRequestError("split_time must be within the subtitle's time range")

    before_snap = _snapshot(subtitle)
    original_end = subtitle.end_time
    original_index = subtitle.sentence_index
    cur_words = subtitle.words or []
    before_words = [w for w in cur_words if float(w.get("start", 0)) < payload.split_time]
    after_words = [w for w in cur_words if float(w.get("start", 0)) >= payload.split_time]

    # Shift subsequent subtitles up by one to free up original_index + 1.
    await db.execute(
        update(Subtitle)
        .where(
            Subtitle.video_id == video_id,
            Subtitle.sentence_index > original_index,
        )
        .values(sentence_index=Subtitle.sentence_index + 1)
    )

    # Original → before part.
    subtitle.text_en = payload.text_before
    subtitle.end_time = payload.split_time
    subtitle.words = before_words or None
    levels = annotate_text(subtitle.text_en)
    subtitle.word_levels = levels or None

    after_snap = _snapshot(subtitle)
    scope = await _determine_edit_scope(db, video_id)
    await _write_revision(db, subtitle, before_snap, after_snap, edited_by=edited_by, scope=scope)

    # New → after part.
    new_sub = Subtitle(
        video_id=video_id,
        start_time=payload.split_time,
        end_time=original_end,
        text_en=payload.text_after,
        text_zh=None,  # translation can't be auto-split; user re-translates
        sentence_index=original_index + 1,
        words=after_words or None,
        speaker=subtitle.speaker,
    )
    new_levels = annotate_text(new_sub.text_en)
    new_sub.word_levels = new_levels or None
    db.add(new_sub)

    await db.commit()
    await db.refresh(subtitle)
    await db.refresh(new_sub)
    await invalidate_video_detail_cache(video_id)
    return [SubtitleResponse.model_validate(subtitle), SubtitleResponse.model_validate(new_sub)]


async def merge_subtitle(
    db: AsyncSession,
    video_id: str,
    subtitle_id: str,
    *,
    edited_by: str | None = None,
) -> SubtitleResponse:
    """Merge a subtitle with the next one (by ``sentence_index``).

    The next subtitle's text/words/timing are folded into the current one and
    the next row is deleted. ``sentence_index`` of subtitles after the deleted
    row is shifted down by one. Returns the merged subtitle (refreshed).
    """
    from sqlalchemy import update

    from app.models.subtitle import Subtitle
    from app.services.ecdict import annotate_text

    result = await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id))
    cur = result.scalar_one_or_none()
    if cur is None:
        raise NotFoundError("Subtitle not found")
    if cur.video_id != video_id:
        raise BadRequestError("Subtitle does not belong to this video")

    nxt_result = await db.execute(
        select(Subtitle)
        .where(
            Subtitle.video_id == video_id,
            Subtitle.sentence_index > cur.sentence_index,
        )
        .order_by(Subtitle.sentence_index)
        .limit(1)
    )
    nxt = nxt_result.scalar_one_or_none()
    if nxt is None:
        raise BadRequestError("No next subtitle to merge with")

    before_snap = _snapshot(cur)
    next_index = nxt.sentence_index

    cur.text_en = (cur.text_en + " " + nxt.text_en).strip()
    cur.end_time = nxt.end_time
    merged_words = (cur.words or []) + (nxt.words or [])
    cur.words = merged_words or None
    if cur.text_zh and nxt.text_zh:
        cur.text_zh = (cur.text_zh + " " + nxt.text_zh).strip()
    elif nxt.text_zh:
        cur.text_zh = nxt.text_zh
    levels = annotate_text(cur.text_en)
    cur.word_levels = levels or None

    await db.delete(nxt)
    await db.flush()  # persist the delete before the index shift

    await db.execute(
        update(Subtitle)
        .where(
            Subtitle.video_id == video_id,
            Subtitle.sentence_index > next_index,
        )
        .values(sentence_index=Subtitle.sentence_index - 1)
    )

    after_snap = _snapshot(cur)
    scope = await _determine_edit_scope(db, video_id)
    await _write_revision(db, cur, before_snap, after_snap, edited_by=edited_by, scope=scope)

    await commit_refresh(db, cur)
    await invalidate_video_detail_cache(video_id)
    return SubtitleResponse.model_validate(cur)


async def recompute_word_levels(
    db: AsyncSession,
    video_id: str,
    subtitle_ids: list[str] | None = None,
) -> dict:
    """Recompute word_levels from ECDICT for selected subtitles (or the whole video).

    Mirrors the finalize pipeline's annotating step and the backfill script.
    Gracefully degrades when ECDICT is unavailable (returns zero counts, no 500).
    """
    from app.models.subtitle import Subtitle
    from app.services.ecdict import annotate_text, is_available

    if not is_available():
        return {"subtitles_updated": 0, "exam_words_found": 0}

    stmt = select(Subtitle).where(Subtitle.video_id == video_id)
    if subtitle_ids is not None:
        if not subtitle_ids:
            return {"subtitles_updated": 0, "exam_words_found": 0}
        stmt = stmt.where(Subtitle.id.in_(subtitle_ids))

    result = await db.execute(stmt)
    subtitles = result.scalars().all()

    updated = 0
    exam_words_found = 0
    for sub in subtitles:
        levels = annotate_text(sub.text_en)
        sub.word_levels = levels or None
        updated += 1
        if levels:
            exam_words_found += len(levels)

    await db.commit()
    await invalidate_video_detail_cache(video_id)
    return {"subtitles_updated": updated, "exam_words_found": exam_words_found}


def _revision_to_dict(r) -> dict:
    """Serialize a SubtitleRevision for the history endpoints."""
    return {
        "id": r.id,
        "subtitle_id": r.subtitle_id,
        "video_id": r.video_id,
        "edited_by": r.edited_by,
        "scope": r.scope,
        "before": r.before,
        "after": r.after,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


async def rollback_subtitle(
    db: AsyncSession,
    video_id: str,
    subtitle_id: str,
    revision_id: str,
    *,
    edited_by: str | None = None,
) -> SubtitleResponse:
    """Roll back a subtitle to the ``before`` state captured in a prior revision.

    Writes a new SubtitleRevision recording the rollback (so history is itself
    audited and reversible). The target revision must belong to this subtitle.
    """
    from app.models.subtitle import Subtitle
    from app.models.subtitle_revision import SubtitleRevision

    result = await db.execute(
        select(SubtitleRevision).where(
            SubtitleRevision.id == revision_id,
            SubtitleRevision.subtitle_id == subtitle_id,
        )
    )
    revision = result.scalar_one_or_none()
    if revision is None:
        raise NotFoundError("Revision not found")
    if revision.video_id != video_id:
        raise BadRequestError("Revision does not belong to this video")

    result = await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id))
    subtitle = result.scalar_one_or_none()
    if subtitle is None:
        raise NotFoundError("Subtitle not found")

    before_snap = _snapshot(subtitle)

    # Apply the prior 'before' values back onto the subtitle.
    for field, old_value in revision.before.items():
        setattr(subtitle, field, old_value)

    # ADM-13: every other write path validates timing; rollback was the one
    # gap. If a neighbor moved since the original edit, restoring the old
    # start/end can overlap it — which would silently corrupt the timeline for
    # playback and make later edits fail validation. Roll the transaction back
    # (no partial state) and answer 409 with guidance instead.
    try:
        await _validate_timing(db, video_id, subtitle)
    except BadRequestError as exc:
        await db.rollback()
        raise ConflictError(
            f"回滚后的时间轴与相邻字幕冲突，已取消回滚：{exc.message}。请先修正相邻字幕时间后重试"
        ) from exc

    after_snap = _snapshot(subtitle)

    scope = await _determine_edit_scope(db, video_id)
    await _write_revision(db, subtitle, before_snap, after_snap, edited_by=edited_by, scope=scope)

    await commit_refresh(db, subtitle)
    await invalidate_video_detail_cache(video_id)
    return SubtitleResponse.model_validate(subtitle)


async def list_subtitle_revisions(
    db: AsyncSession,
    video_id: str,
    *,
    subtitle_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """List subtitle edit revisions for a video (optionally filtered to one subtitle).

    Returns the standard paginated envelope (items/page/page_size/has_more/total),
    newest first. ``total`` (ADM-10) is the full filtered count so the admin UI
    can render "共 N 条" instead of only "has more". Ordering adds ``id`` as a
    tiebreaker so equal ``created_at`` timestamps (batch imports / bulk edits in
    the same second) cannot make rows repeat or vanish across pages.
    """
    from app.models.subtitle_revision import SubtitleRevision

    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    offset = (page - 1) * page_size

    filters = [SubtitleRevision.video_id == video_id]
    if subtitle_id is not None:
        filters.append(SubtitleRevision.subtitle_id == subtitle_id)

    total = (await db.scalar(select(func.count()).select_from(SubtitleRevision).where(*filters))) or 0

    stmt = (
        select(SubtitleRevision)
        .where(*filters)
        .order_by(SubtitleRevision.created_at.desc(), SubtitleRevision.id.desc())
        .offset(offset)
        .limit(page_size + 1)
    )

    result = await db.execute(stmt)
    rows = result.scalars().all()
    has_more = len(rows) > page_size
    items = rows[:page_size]

    return paginated(
        [_revision_to_dict(r) for r in items],
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


# ---------------------------------------------------------------------------
# Bulk re-segmentation (admin) — snapshot, re-cut, rollback
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# User-data preservation across wholesale subtitle replacement (ADM-01)
# ---------------------------------------------------------------------------
#
# Re-segmenting (and rolling back) replaces every subtitle row with new ids.
# Three user-owned things hang off ``subtitles.id`` and used to be destroyed by
# the DB cascades without a trace:
#
#   * ``sentence_favorites.subtitle_id``     ON DELETE CASCADE  → user收藏消失
#   * ``subtitle_revisions.subtitle_id``     ON DELETE CASCADE  → 编辑历史归零
#   * ``vocabulary.subtitle_id``             ON DELETE SET NULL → 来源句断链
#
# The helpers below capture those rows before the swap, re-attach them to new
# rows by time overlap, and mirror the cascades explicitly for whatever could
# not be mapped (so the behaviour is the same on Postgres and on the SQLite
# test DB). Rows that cannot be mapped are also serialised into the snapshot
# JSON (``user_data.lost``) so a rollback can restore them.


async def _capture_subtitle_user_data(db: AsyncSession, video_id: str, subtitle_ids: list[str]) -> _UserDataCapture:
    """Snapshot favorites / revision history / vocabulary links before the swap."""
    from app.models.learning import Vocabulary
    from app.models.user_content import SentenceFavorite

    capture = _UserDataCapture()
    if not subtitle_ids:
        return capture
    id_set = set(subtitle_ids)

    favorites = (
        (await db.execute(select(SentenceFavorite).where(SentenceFavorite.subtitle_id.in_(subtitle_ids))))
        .scalars()
        .all()
    )
    capture.favorites = [
        {
            "id": row.id,
            "user_id": row.user_id,
            "subtitle_id": row.subtitle_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in favorites
    ]

    revisions = (
        (await db.execute(select(SubtitleRevision).where(SubtitleRevision.video_id == video_id))).scalars().all()
    )
    capture.revisions = [
        {
            "id": row.id,
            "subtitle_id": row.subtitle_id,
            "video_id": row.video_id,
            "edited_by": row.edited_by,
            "scope": row.scope,
            "before": row.before,
            "after": row.after,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in revisions
        if row.subtitle_id in id_set
    ]

    vocabulary = (await db.execute(select(Vocabulary).where(Vocabulary.subtitle_id.in_(subtitle_ids)))).scalars().all()
    capture.vocabulary = [{"id": row.id, "user_id": row.user_id, "subtitle_id": row.subtitle_id} for row in vocabulary]
    return capture


async def _apply_remap_plan(db: AsyncSession, plan: _RemapPlan) -> None:
    """Point the captured rows at their new subtitle ids (before old rows die)."""
    from app.models.learning import Vocabulary
    from app.models.user_content import SentenceFavorite

    for new_id, ids in plan.favorites_move.items():
        await db.execute(update(SentenceFavorite).where(SentenceFavorite.id.in_(ids)).values(subtitle_id=new_id))
    for new_id, ids in plan.revisions_move.items():
        await db.execute(update(SubtitleRevision).where(SubtitleRevision.id.in_(ids)).values(subtitle_id=new_id))
    for new_id, ids in plan.vocabulary_move.items():
        await db.execute(update(Vocabulary).where(Vocabulary.id.in_(ids)).values(subtitle_id=new_id))


async def _drop_user_data_for_removed_subtitles(db: AsyncSession, subtitle_ids: list[str]) -> None:
    """Mirror the DB cascades explicitly for subtitles that are about to go.

    Postgres applies these itself (CASCADE / SET NULL), but the SQLite test DB
    does not enforce foreign keys — doing the statements ourselves keeps
    production and tests on one behaviour and makes the lossy part explicit
    (rows that were not remapped are deleted / unlinked here, and recorded in
    the snapshot by the caller).
    """
    from app.models.learning import Vocabulary
    from app.models.user_content import SentenceFavorite

    if not subtitle_ids:
        return
    await db.execute(delete(SentenceFavorite).where(SentenceFavorite.subtitle_id.in_(subtitle_ids)))
    await db.execute(delete(SubtitleRevision).where(SubtitleRevision.subtitle_id.in_(subtitle_ids)))
    await db.execute(update(Vocabulary).where(Vocabulary.subtitle_id.in_(subtitle_ids)).values(subtitle_id=None))


async def _restore_lost_user_data(db: AsyncSession, lost: dict, restored_id_by_old: dict[str, str]) -> dict[str, int]:
    """Re-insert rows the original re-segmentation could not map.

    ``lost`` holds rows keyed by their ORIGINAL subtitle id; the caller passes
    the original-id → restored-row-id map. Only rows whose original subtitle is
    part of this snapshot can be restored; the rest stay in the snapshot JSON.
    """
    from app.models.learning import Vocabulary
    from app.models.user_content import SentenceFavorite

    restored = {"favorites": 0, "revisions": 0, "vocabulary": 0}

    favorite_rows = [row for row in lost.get("favorites", []) if restored_id_by_old.get(str(row.get("subtitle_id")))]
    if favorite_rows:
        target_ids = {restored_id_by_old[row["subtitle_id"]] for row in favorite_rows}
        existing_rows = (
            await db.execute(
                select(SentenceFavorite.user_id, SentenceFavorite.subtitle_id).where(
                    SentenceFavorite.subtitle_id.in_(target_ids)
                )
            )
        ).all()
        existing: set[tuple[str, str]] = {(row[0], row[1]) for row in existing_rows}
        for row in favorite_rows:
            favorite_new_id = restored_id_by_old[row["subtitle_id"]]
            key = (row["user_id"], favorite_new_id)
            if key in existing:
                continue
            db.add(
                SentenceFavorite(
                    id=row["id"],
                    user_id=row["user_id"],
                    subtitle_id=favorite_new_id,
                    created_at=_parse_snapshot_dt(row.get("created_at")),
                )
            )
            existing.add(key)
            restored["favorites"] += 1

    revision_rows = [row for row in lost.get("revisions", []) if restored_id_by_old.get(str(row.get("subtitle_id")))]
    if revision_rows:
        existing_ids = set(
            (
                await db.execute(
                    select(SubtitleRevision.id).where(SubtitleRevision.id.in_([row["id"] for row in revision_rows]))
                )
            )
            .scalars()
            .all()
        )
        for row in revision_rows:
            if row["id"] in existing_ids:
                continue
            db.add(
                SubtitleRevision(
                    id=row["id"],
                    subtitle_id=restored_id_by_old[row["subtitle_id"]],
                    video_id=row.get("video_id"),
                    edited_by=row.get("edited_by"),
                    scope=row.get("scope") or "fork",
                    before=row.get("before") or {},
                    after=row.get("after") or {},
                    created_at=_parse_snapshot_dt(row.get("created_at")),
                )
            )
            existing_ids.add(row["id"])
            restored["revisions"] += 1

    for row in lost.get("vocabulary", []):
        vocabulary_new_id = restored_id_by_old.get(str(row.get("subtitle_id")))
        if vocabulary_new_id is None:
            continue
        result = await db.execute(
            update(Vocabulary)
            .where(Vocabulary.id == row["id"], Vocabulary.subtitle_id.is_(None))
            .values(subtitle_id=vocabulary_new_id)
        )
        # ``rowcount`` may be -1 when the driver does not report it; clamp so
        # the counter can never go negative.
        restored["vocabulary"] += max(0, int(getattr(result, "rowcount", 0) or 0))

    return restored


async def resegment_video(
    db: AsyncSession,
    video_id: str,
    *,
    edited_by: str | None = None,
) -> dict:
    """Re-segment every subtitle of a video while preserving user data (ADM-01).

    Snapshots the current subtitles (so the change is reversible), re-cuts
    them into proper sentences, and replaces the rows. Translations (text_zh)
    are dropped because the English segmentation changed — the admin can
    re-trigger translation afterwards.

    Sentence favorites, edit revisions and vocabulary source links are captured
    before the swap and re-attached to the new segments by time overlap (see the
    helpers above); the response reports exactly what happened. Nothing is
    dropped silently: unmappable rows are kept inside the snapshot JSON
    (``user_data.lost``) and restored by ``rollback_resegment``.

    Returns the ``ResegmentResult`` payload: ``{before_count, after_count,
    translations_cleared, snapshot_id, favorites_*, revisions_*, vocabulary_*}``.
    """
    from app.models.subtitle import Subtitle
    from app.models.subtitle_resegment_snapshot import SubtitleResegmentSnapshot
    from app.services.ecdict import annotate_text

    result = await db.execute(select(Subtitle).where(Subtitle.video_id == video_id).order_by(Subtitle.sentence_index))
    subs = list(result.scalars().all())
    if not subs:
        raise BadRequestError("视频没有字幕，无法重断句")

    new_segs = _resegment_segments(subs)
    if not new_segs:
        raise BadRequestError("重断句失败：无法从现有字幕生成新分段")

    old_ids = [s.id for s in subs]
    capture = await _capture_subtitle_user_data(db, video_id, old_ids)

    # Pre-generate ids so user data can be re-pointed before anything is
    # flushed: no need to read generated defaults back from the DB.
    new_rows = [
        Subtitle(
            id=str(uuid.uuid4()),
            video_id=video_id,
            start_time=seg["start"],
            end_time=seg["end"],
            text_en=seg["text"],
            text_zh=None,  # translations cleared — segmentation changed
            sentence_index=index,
            words=seg.get("words"),
            word_levels=annotate_text(seg["text"]) or None,
        )
        for index, seg in enumerate(new_segs)
    ]

    id_by_old: dict[str, str | None] = {}
    for old in subs:
        index = _map_interval_to_segment(old.start_time, old.end_time, new_segs)
        id_by_old[old.id] = new_rows[index].id if index is not None else None

    plan = _build_remap_plan(capture, id_by_old)

    snapshot = SubtitleResegmentSnapshot(
        video_id=video_id,
        segments_json=_snapshot_payload(
            [_subtitle_snapshot_dict(s) for s in subs],
            id_by_old,
            capture,
            plan,
        ),
        before_count=len(subs),
        applied_by=edited_by,
    )
    db.add(snapshot)
    for row in new_rows:
        db.add(row)
    await db.flush()  # new rows exist → the remap UPDATEs satisfy the FKs

    await _apply_remap_plan(db, plan)
    await db.flush()

    await _drop_user_data_for_removed_subtitles(db, old_ids)
    for old in subs:
        await db.delete(old)
    await db.flush()

    snapshot.after_count = len(new_rows)
    await db.commit()
    await invalidate_video_detail_cache(video_id)

    return {
        "before_count": len(subs),
        "after_count": len(new_rows),
        "translations_cleared": True,
        "snapshot_id": snapshot.id,
        "favorites_total": len(capture.favorites),
        "revisions_total": len(capture.revisions),
        "vocabulary_total": len(capture.vocabulary),
        **_remap_counts(plan),
    }


async def rollback_resegment(
    db: AsyncSession,
    video_id: str,
    *,
    edited_by: str | None = None,
) -> dict:
    """Restore subtitles from the latest re-segment snapshot (ADM-01 reverse).

    Deletes the current (re-segmented) subtitles and re-inserts the snapshotted
    rows, including their translations. User data attached to the current rows
    is re-mapped back onto the restored rows by time overlap (same helper as the
    forward direction), and rows that the original re-segmentation had to drop
    are re-inserted from the snapshot payload. The snapshot is marked rolled
    back, so the mapping is never applied twice.
    """
    from app.models.subtitle import Subtitle
    from app.models.subtitle_resegment_snapshot import SubtitleResegmentSnapshot

    result = await db.execute(
        select(SubtitleResegmentSnapshot)
        .where(
            SubtitleResegmentSnapshot.video_id == video_id,
            SubtitleResegmentSnapshot.rolled_back.is_(False),
        )
        .order_by(SubtitleResegmentSnapshot.applied_at.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        raise BadRequestError("没有可回滚的重断句快照")

    segments, meta = _parse_snapshot_payload(snapshot.segments_json)
    if not segments:
        raise BadRequestError("重断句快照为空，无法回滚")

    cur_rows = list(
        (await db.execute(select(Subtitle).where(Subtitle.video_id == video_id).order_by(Subtitle.sentence_index)))
        .scalars()
        .all()
    )
    cur_ids = [row.id for row in cur_rows]
    capture = await _capture_subtitle_user_data(db, video_id, cur_ids)

    restored_rows = [
        Subtitle(
            id=str(uuid.uuid4()),
            video_id=video_id,
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            text_en=seg["text_en"],
            text_zh=seg.get("text_zh"),
            sentence_index=seg["sentence_index"],
            words=seg.get("words"),
            grammar_note=seg.get("grammar_note"),
            speaker=seg.get("speaker"),
            word_levels=seg.get("word_levels"),
        )
        for seg in segments
    ]
    id_by_cur: dict[str, str | None] = {}
    for row in cur_rows:
        index = _map_interval_to_segment(row.start_time, row.end_time, segments)
        id_by_cur[row.id] = restored_rows[index].id if index is not None else None
    plan = _build_remap_plan(capture, id_by_cur)
    # Original (snapshot-time) subtitle id → the row it is being restored as.
    restored_id_by_old = {seg["id"]: row.id for seg, row in zip(segments, restored_rows, strict=False) if seg.get("id")}

    for row in restored_rows:
        db.add(row)
    await db.flush()  # restored rows exist → the remap UPDATEs satisfy the FKs

    await _apply_remap_plan(db, plan)
    await db.flush()

    # Rows the forward re-segmentation could not map are not attached to any
    # current subtitle; bring them back from the snapshot payload.
    lost = (meta.get("user_data") or {}).get("lost") or {}
    lost_counts = await _restore_lost_user_data(db, lost, restored_id_by_old)

    await _drop_user_data_for_removed_subtitles(db, cur_ids)
    for row in cur_rows:
        await db.delete(row)
    await db.flush()

    snapshot.rolled_back = True
    snapshot.rolled_back_at = datetime.now(UTC)
    await db.commit()
    await invalidate_video_detail_cache(video_id)

    counts = _remap_counts(plan)
    return {
        "restored_count": len(restored_rows),
        "snapshot_id": snapshot.id,
        "favorites_remapped": counts["favorites_remapped"],
        "favorites_unmatched": counts["favorites_unmatched"],
        "favorites_restored_from_snapshot": lost_counts["favorites"],
        "revisions_preserved": counts["revisions_preserved"],
        "revisions_unmatched": counts["revisions_unmatched"],
        "revisions_restored_from_snapshot": lost_counts["revisions"],
        "vocabulary_relinked": counts["vocabulary_relinked"],
        "vocabulary_unmatched": counts["vocabulary_unmatched"],
        "vocabulary_restored_from_snapshot": lost_counts["vocabulary"],
    }

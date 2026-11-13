"""Seed a minimal official "ready" video + bilingual subtitles for CI e2e tests.

The Playwright watch-page tests skip when the home page has no video link; CI
starts from an empty database, so without a seed those tests never execute in
CI (the core watch journey was silently uncovered). This script creates one
official ready video with subtitles — no network, no GPU, no media file — and
is idempotent (exits 0 if a suitable video already exists).

Usage:
    cd backend && python scripts/seed_e2e.py

Runs against the configured DATABASE_URL (CI sets it for the e2e job).
"""

import asyncio
import math
import struct
import sys
import wave
import zlib
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

# Make `app` importable when run as `python scripts/seed_e2e.py` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import async_session
from app.models.channel import Channel
from app.models.exam_test import ExamPaper, ExamQuestion
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoReviewStatus, VideoSource, VideoStatus

TITLE = "E2E Demo Video · a reading habit (CI seed)"
# Databases seeded before 2026-11-12 carry this name; matched as a fallback so an
# upgrade rewrites the row instead of inserting a second demo video.
_LEGACY_TITLE = "E2E Demo Video (CI seed)"

# Media files are gitignored; the seed writes them so the listening spec has a
# real, seekable audio track and the home editorial card has a decodable cover.
_MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"
_THUMBNAIL_PATH = "/media/e2e-thumb.png"
_LISTENING_TITLE = "Action Verbs A2 · E2E listening"
_LISTENING_SUBTITLES = [
    (1.0, 5.0, "I walk into the office every morning.", "我每天早上走进办公室。"),
    (6.0, 10.0, "She reads the news before breakfast.", "她在早餐前看新闻。"),
    (11.0, 15.0, "They practice listening every single day.", "他们每天都练习听力。"),
]
_CHANNEL_SLUG = "e2e-channel"

# Distinctive set_no so the demo paper never collides with real imported papers.
_E2E_PAPER_KEY = dict(level="cet4", year=2020, month=1, set_no=99)

# Covers all three reading sections: cloze (options derived from the
# [word bank] appendix), matching (options derived from paragraph letters),
# and plain multiple-choice reading_C. The e2e exam spec answers every
# question, so a section without answerable options would fail the run.
_E2E_QUESTIONS = [
    {
        "section": "reading_A",
        "number": 26,
        "question_type": "cloze",
        "passage": (
            "The team 26 a new plan to improve service quality.\n\n"
            "Customers often 27 when support takes too long."
            "\n\n[word bank]\nA) launched\nB) complain\nC) celebrate"
        ),
        "question": None,
        "options": None,
        "answer": "A",
        "explanation": "launched 符合语境（启动新计划）。",
    },
    {
        "section": "reading_A",
        "number": 27,
        "question_type": "cloze",
        "passage": "",
        "question": None,
        "options": None,
        "answer": "B",
        "explanation": "complain 符合语境（抱怨等待太久）。",
    },
    {
        "section": "reading_B",
        "number": 36,
        "question_type": "matching",
        "passage": (
            "A) The first paragraph describes an early experiment.\n\n"
            "B) The second paragraph reports the final results.\n\n"
            "C) The third paragraph lists future directions."
        ),
        "question": "Which paragraph reports the final results?",
        "options": None,
        "answer": "B",
        "explanation": "段落 B 描述了最终结果。",
    },
    {
        "section": "reading_B",
        "number": 37,
        "question_type": "matching",
        "passage": "",
        "question": "Which paragraph lists future directions?",
        "options": None,
        "answer": "C",
        "explanation": "段落 C 描述了未来方向。",
    },
    {
        "section": "reading_C",
        "number": 46,
        "question_type": "reading",
        "passage": "Regular exercise improves both physical and mental health.",
        "question": "What does the passage say about exercise?",
        "options": {
            "A": "It only helps the body.",
            "B": "It improves physical and mental health.",
            "C": "It has no proven benefit.",
            "D": "It replaces medical treatment.",
        },
        "answer": "B",
        "explanation": "原文直接说明锻炼改善身心。",
    },
    {
        "section": "reading_C",
        "number": 47,
        "question_type": "reading",
        "passage": "",
        "question": "What is the tone of the passage?",
        "options": {
            "A": "Informative.",
            "B": "Sarcastic.",
            "C": "Doubtful.",
            "D": "Humorous.",
        },
        "answer": "A",
        "explanation": "说明性语气。",
    },
]

# (start, end, en, zh) — four short bilingual sentences so the watch page has
# something to render and subtitle navigation has room to move.
#
# `habit` appears in the last sentence on purpose: design-rollout.spec.ts:139
# searches for that word and asserts the four group headings render. Without a
# hit the search page shows its empty state instead, and the headings do not
# exist at all — that is the page's designed behaviour, so the fixture is what
# has to carry the word (the alternative, shipping ECDICT to CI, is an 850 MB
# download for one assertion). Keep it: this is not decoration.
_DEMO_SUBTITLES = [
    (0.0, 4.2, "Hello and welcome to today's lesson.", "大家好，欢迎来到今天的课程。"),
    (4.2, 8.5, "Today we are going to practice English together.", "今天我们将一起练习英语。"),
    (8.5, 12.0, "Remember to repeat each sentence out loud.", "记住要大声重复每个句子。"),
    (
        12.0,
        16.0,
        "This is the last sentence of the demo: reading daily is a good habit.",
        "这是演示的最后一句：每天阅读是个好习惯。",
    ),
]

# The two group headings design-rollout.spec.ts:139 also asserts need one hit
# each, and their sources are not the subtitle text: the video group matches
# title/title_zh/topic_tags, the channel group matches name/description.
# One word (`habit`) scores all four groups at once, which keeps the search
# page from collapsing into its all-empty state. Both are spelled out here
# because TITLE is defined before this block.
_DEMO_CHANNEL_DESCRIPTION = "Seeded channel for the e2e library/persistence spec; daily reading habit."


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _write_thumbnail() -> None:
    """A deterministic 320x180 PNG so the editorial card renders a real <img>."""
    width, height = 320, 180
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # PNG filter: none
        for x in range(width):
            raw += bytes((30 + x * 200 // width, 60 + y * 150 // height, 120))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )
    _MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    (_MEDIA_DIR / "e2e-thumb.png").write_bytes(png)


def _write_tone(path: Path, seconds: int = 20) -> None:
    """16-bit mono WAV tone: enough for a 20s listening-clip session."""
    rate = 16_000
    amplitude = int(0.06 * 32767)
    frames = bytearray()
    for index in range(rate * seconds):
        frames += struct.pack("<h", int(amplitude * math.sin(2 * math.pi * 440 * index / rate)))
    _MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(frames))


async def seed_exam_paper(db) -> None:
    """Idempotent: one demo paper so the exam e2e spec has a full journey."""
    existing = await db.scalar(select(ExamPaper).filter_by(**_E2E_PAPER_KEY))
    if existing is not None:
        print(f"seed_e2e: exam paper already present ({existing.id}) — skipping")
        return
    paper = ExamPaper(
        **_E2E_PAPER_KEY,
        title="E2E Demo Paper (CI seed)",
        source="seed_e2e",
        total_questions=len(_E2E_QUESTIONS),
    )
    db.add(paper)
    await db.flush()
    # Section A cloze shares one passage; matching shares one too. Repeat
    # questions carry an empty passage and inherit the section's passage at
    # render time (ExamRunner groups by section). Fill the shared passage
    # into the first question of each section only.
    seen_sections: set[str] = set()
    for q in _E2E_QUESTIONS:
        passage = q["passage"]
        if q["section"] in seen_sections:
            passage = ""
        seen_sections.add(q["section"])
        db.add(
            ExamQuestion(
                paper_id=paper.id,
                section=q["section"],
                number=q["number"],
                question_type=q["question_type"],
                passage=passage or None,
                question=q["question"],
                options=q["options"],
                answer=q["answer"],
                explanation=q["explanation"],
            )
        )
    print(f"seed_e2e: created exam paper {paper.id} with {len(_E2E_QUESTIONS)} questions")


async def seed_video(db) -> Video:
    """Idempotent: one official ready video so the watch e2e spec can run."""
    # A database seeded before the title carried `habit` holds the old name.
    # Match either, otherwise upgrading a long-lived local database would
    # insert a second demo video and every watch spec would see two.
    video = await db.scalar(select(Video).where(Video.title.in_([TITLE, _LEGACY_TITLE])))
    if video is None:
        video = Video(
            title=TITLE,
            source_url="https://example.com/e2e-demo.mp4",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            review_status=VideoReviewStatus.published.value,
            is_official=True,
            is_published=True,
            is_featured=True,
            show_on_homepage=True,
            duration=16.0,
        )
        db.add(video)
        await db.flush()
        for i, (start, end, en, zh) in enumerate(_DEMO_SUBTITLES):
            db.add(
                Subtitle(
                    video_id=video.id,
                    start_time=start,
                    end_time=end,
                    text_en=en,
                    text_zh=zh,
                    sentence_index=i,
                )
            )
        print(f"seed_e2e: created official ready video {video.id} with {len(_DEMO_SUBTITLES)} subtitles")
    else:
        print(f"seed_e2e: official ready video already present ({video.id})")
        # Same reason as the title: `habit` has to reach an already-seeded row
        # so the search page renders its group headings instead of empty state.
        if video.title != TITLE:
            video.title = TITLE
        for i, (_, _, en, zh) in enumerate(_DEMO_SUBTITLES):
            row = await db.scalar(select(Subtitle).where(Subtitle.video_id == video.id, Subtitle.sentence_index == i))
            if row is not None and row.text_en != en:
                row.text_en, row.text_zh = en, zh

    # Placeholder media URL — the e2e suite asserts page behavior, not
    # playback; the file itself is not required (no file ⇒ playable guards skip).
    video.video_url_720p = f"/media/{video.id}.mp4"
    # Real cover: the home editorial card only renders an <img> with a URL.
    video.thumbnail_url = _THUMBNAIL_PATH
    _write_thumbnail()
    return video


async def seed_channel(db, video: Video) -> Channel:
    """Idempotent: one visible channel owning the demo video (library e2e)."""
    channel = await db.scalar(select(Channel).where(Channel.slug == _CHANNEL_SLUG))
    if channel is None:
        channel = Channel(
            name="E2E Channel",
            slug=_CHANNEL_SLUG,
            description=_DEMO_CHANNEL_DESCRIPTION,
            is_visible=True,
        )
        db.add(channel)
        await db.flush()
        print(f"seed_e2e: created channel {channel.id} ({channel.slug})")
    elif channel.description != _DEMO_CHANNEL_DESCRIPTION:
        # The search group heading assertion needs `habit` to reach the channel
        # row too. A database seeded before that word was added keeps the old
        # description, so rewrite it instead of only filling new rows.
        channel.description = _DEMO_CHANNEL_DESCRIPTION
    video.channel_ref = channel.id
    # The watch page's channel block renders from the scraped channel_name
    # column (not the Channel row), so seed both halves of the link.
    video.channel_name = channel.name
    return channel


async def seed_listening_video(db) -> None:
    """Idempotent: a published video with real WAV audio for the listening spec.

    A separate row keeps the main demo video intentionally non-playable, so the
    existing mobile media guards keep skipping exactly as before.
    """
    video = await db.scalar(select(Video).where(Video.title == _LISTENING_TITLE))
    if video is None:
        video = Video(
            title=_LISTENING_TITLE,
            source_url="https://example.com/e2e-listening.wav",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            review_status=VideoReviewStatus.published.value,
            is_official=True,
            is_published=True,
            is_featured=False,
            show_on_homepage=False,
            duration=20.0,
            published_at=datetime(2020, 1, 1, tzinfo=UTC),
        )
        db.add(video)
        await db.flush()
        for i, (start, end, en, zh) in enumerate(_LISTENING_SUBTITLES):
            db.add(
                Subtitle(
                    video_id=video.id,
                    start_time=start,
                    end_time=end,
                    text_en=en,
                    text_zh=zh,
                    sentence_index=i,
                )
            )
        print(f"seed_e2e: created listening video {video.id} with {len(_LISTENING_SUBTITLES)} cues")
    # Rewrite the URL + audio every run so a broken fixture self-heals.
    _write_tone(_MEDIA_DIR / f"{video.id}.wav")
    video.video_url_720p = f"/media/{video.id}.wav"


async def _invalidate_detail_cache(video_ids: list[str]) -> None:
    """Drop cached watch-page payloads after changing seed rows.

    A long-lived dev/CI Redis otherwise keeps serving the pre-seed detail (no
    channel link), which is indistinguishable from a product regression.
    """
    try:
        from redis.asyncio import Redis

        from app.core.config import get_settings

        client = Redis.from_url(get_settings().redis_url, decode_responses=True)
        await client.delete(*[f"video:detail:{video_id}" for video_id in video_ids])
        await client.close()
    except Exception as exc:  # cache is optional for seeding
        print(f"seed_e2e: cache invalidation skipped ({exc})")


async def main() -> int:
    async with async_session() as db:
        video = await seed_video(db)
        await seed_channel(db, video)
        await seed_listening_video(db)
        await seed_exam_paper(db)
        await db.commit()
        await _invalidate_detail_cache([video.id])
        return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as exc:  # fail loudly — CI depends on this seed
        print(f"seed_e2e: FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

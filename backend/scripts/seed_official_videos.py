"""Seed official videos for the SeeWord app homepage.

Selection criteria (in order of priority):
1. Content quality: Real, natural English conversation/speech; avoid memes/music-only.
2. Engagement: High like_count and comment_count (proxy for quality and interest).
3. Topic diversity: Cover TED, interviews, news, educational, daily life, tech, etc.
4. Stability: Well-known videos less likely to be removed.
5. Duration: 2-20 minutes (optimal for learning sessions).
6. Difficulty spread: From slow/clear (A2) to fast/complex (C1).

Uses yt-dlp to extract metadata + subtitles directly (no Celery needed).
YouTube videos are set to lightweight mode (embed playback, no local file).

Usage:
    cd backend && python scripts/seed_official_videos.py

Requires:
    - PostgreSQL running (docker compose -f docker-compose.dev.yml up -d)
    - yt-dlp installed (pip install yt-dlp)
    - Network access to YouTube (set HTTP_PROXY in .env if behind firewall)
"""

import asyncio
import json
import re
import sys
import tempfile
import uuid
from pathlib import Path

import httpx

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yt_dlp
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoSource, VideoStatus

# Curated YouTube videos selected by engagement metrics (likes + comments).
# Criteria: real English speech, high engagement, 2-20 min duration, diverse topics.
# Sorted by like_count descending within each category.
# Data collected 2026-06-10 via yt-dlp with authenticated cookies.
OFFICIAL_VIDEOS = [
    # TED Talks - structured presentations, highest engagement
    {
        "id": "arj7oStGLkU",
        "category": "ted",
        "title": "Inside the Mind of a Master Procrastinator | Tim Urban",
        "likes": 2049276,
        "comments": 79000,
        "duration_min": 14,
    },
    {
        "id": "H14bBuluwB8",
        "category": "ted",
        "title": "Grit: The Power of Passion and Perseverance | Angela Lee Duckworth",
        "likes": 275698,
        "comments": 6000,
        "duration_min": 6,
    },
    {
        "id": "8jPQjjsBbIc",
        "category": "ted",
        "title": "How to stay calm when you know you'll be stressed | Daniel Levitin",
        "likes": 263278,
        "comments": 4000,
        "duration_min": 12,
    },
    # Interviews - natural conversation, celebrity/professional
    {
        "id": "oX7OduG1YmI",
        "category": "interview",
        "title": "The Future Mark Zuckerberg Is Trying To Build",
        "likes": 134079,
        "comments": 6000,
        "duration_min": 47,
    },
    {
        "id": "6DlrqeWrczs",
        "category": "interview",
        "title": "Oprah Winfrey on Career, Life, and Leadership",
        "likes": 77182,
        "comments": 1300,
        "duration_min": 64,
    },
    {
        "id": "wb6zZfakPJ0",
        "category": "interview",
        "title": "Cillian Murphy: The 60 Minutes Interview",
        "likes": 57493,
        "comments": 3700,
        "duration_min": 13,
    },
    # Educational - explicitly for English learners
    {
        "id": "Ff5FUoo2YZA",
        "category": "educational",
        "title": "Learning English for Beginners: My top tips",
        "likes": 155029,
        "comments": 3500,
        "duration_min": 12,
    },
    {
        "id": "dEcr9M0xKE4",
        "category": "educational",
        "title": "English for Beginner Level: Speak Real English",
        "likes": 104033,
        "comments": 3300,
        "duration_min": 47,
    },
    {
        "id": "MSYw502dJNY",
        "category": "educational",
        "title": "How and Why We Read: Crash Course English Literature",
        "likes": 63851,
        "comments": 6000,
        "duration_min": 7,
    },
    # Vlogs - daily life, casual English
    {
        "id": "m2uOnNe8K3g",
        "category": "vlog",
        "title": "Learn English at Home (Cooking, Daily life) with Comprehensible Input",
        "likes": 15129,
        "comments": 1700,
        "duration_min": 17,
    },
    # Movie Clips - iconic speeches, dramatic delivery
    {
        "id": "kCd6HLNW3MQ",
        "category": "movie",
        "title": "Aunt May's Motivational Speech Scene - Spider-Man: No Way Home",
        "likes": 25866,
        "comments": 4200,
        "duration_min": 3,
    },
    # Speeches - historical, inspirational
    {
        "id": "vP4iY1TtS3s",
        "category": "speech",
        "title": "I Have a Dream speech by Martin Luther King Jr.",
        "likes": 416296,
        "comments": 0,
        "duration_min": 6,
    },
]


def _download_thumbnail(url: str, dest: Path, video_id: str) -> bool:
    """Download a thumbnail image to the local media directory.

    Returns True on success.  Falls back silently on failure (the external
    URL is still stored in the DB and the runtime proxy_image endpoint
    will try to serve it — or the user can upload a local copy later).
    """
    settings = get_settings()
    proxy = settings.http_proxy or None
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True, proxy=proxy) as client:
            resp = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 SeeWord/1.0 (thumbnail download)",
                    "Referer": "https://www.youtube.com/",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
            if resp.status_code != 200:
                print(f"  [WARN] Thumbnail download returned HTTP {resp.status_code}")
                return False
            ct = resp.headers.get("content-type", "")
            if not ct.lower().startswith("image/"):
                print(f"  [WARN] Thumbnail response is not an image: {ct}")
                return False
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.content)
            print(f"  [THUMB] Downloaded to {dest} ({len(resp.content)} bytes)")
            return True
    except Exception as e:
        print(f"  [WARN] Thumbnail download failed: {e}")
        return False


def _extract_youtube_id(url: str) -> str | None:
    m = re.search(
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})", url
    )
    return m.group(1) if m else None


def _fetch_metadata(video_id: str) -> dict | None:
    """Fetch video metadata via yt-dlp (no download)."""
    settings = get_settings()
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if settings.http_proxy:
        opts["proxy"] = settings.http_proxy
    if settings.youtube_cookies_path and Path(settings.youtube_cookies_path).exists():
        opts["cookiefile"] = settings.youtube_cookies_path

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            from app.services.external_meta import pick_best_thumbnail

            return {
                "title": info.get("title", ""),
                "thumbnail": pick_best_thumbnail(info) or "",
                "duration": info.get("duration"),
                "youtube_video_id": video_id,
                "like_count": info.get("like_count"),
                "comment_count": info.get("comment_count"),
                "view_count": info.get("view_count"),
                "uploader": info.get("uploader", ""),
            }
    except Exception as e:
        print(f"  [WARN] Failed to fetch metadata for {video_id}: {e}")
        return None


def _fetch_subtitles(video_id: str) -> list[dict] | None:
    """Fetch English subtitles via yt-dlp (JSON3 preferred, VTT/SRT fallback)."""
    settings = get_settings()
    url = f"https://www.youtube.com/watch?v={video_id}"
    tmpdir = tempfile.mkdtemp(prefix="speaking_seed_")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "subtitlesformat": "json3",
        "outtmpl": f"{tmpdir}/sub",
    }
    if settings.http_proxy:
        opts["proxy"] = settings.http_proxy
    if settings.youtube_cookies_path and Path(settings.youtube_cookies_path).exists():
        opts["cookiefile"] = settings.youtube_cookies_path

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)

        # Find the downloaded subtitle file
        sub_files = list(Path(tmpdir).glob("sub.en.*"))
        if not sub_files:
            # Try VTT/SRT fallback
            opts["subtitlesformat"] = "vtt"
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            sub_files = list(Path(tmpdir).glob("sub.en.*"))

        if not sub_files:
            return None

        sub_path = sub_files[0]
        suffix = sub_path.suffix.lower()

        if suffix == ".json3":
            return _parse_json3(sub_path)
        elif suffix in (".vtt", ".srt"):
            return _parse_vtt(sub_path) if suffix == ".vtt" else _parse_srt(sub_path)
        else:
            return None

    except Exception as e:
        print(f"  [WARN] Failed to fetch subtitles for {video_id}: {e}")
        return None
    finally:
        # Cleanup temp dir
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


def _parse_json3(path: Path) -> list[dict]:
    """Parse YouTube JSON3 subtitle format."""
    data = json.loads(path.read_text("utf-8"))
    subs = []
    for ev in data.get("events", []):
        if "segs" not in ev or ev.get("aAppend"):
            continue
        words = [s["utf8"] for s in ev["segs"] if "utf8" in s]
        if not words:
            continue
        text = " ".join(w.strip() for w in words).strip()
        if text:
            subs.append(
                {
                    "start": ev["tStartMs"] / 1000,
                    "end": (ev["tStartMs"] + ev.get("dDurationMs", 0)) / 1000,
                    "text": text,
                }
            )
    return subs


def _parse_vtt(path: Path) -> list[dict]:
    """Parse WebVTT subtitle format."""
    subs = []
    lines = path.read_text("utf-8").splitlines()
    time_pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})")
    current_text = []
    current_start = None
    current_end = None

    for line in lines:
        m = time_pattern.search(line)
        if m:
            # Save previous subtitle
            if current_text and current_start is not None:
                text = " ".join(current_text).strip()
                if text:
                    subs.append({"start": current_start, "end": current_end, "text": text})
            current_start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000
            current_end = int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8)) / 1000
            current_text = []
        elif line.strip() and not line.startswith("WEBVTT") and not line.startswith("Kind:"):
            current_text.append(line.strip())

    # Don't forget the last one
    if current_text and current_start is not None:
        text = " ".join(current_text).strip()
        if text:
            subs.append({"start": current_start, "end": current_end, "text": text})

    return subs


def _parse_srt(path: Path) -> list[dict]:
    """Parse SRT subtitle format."""
    subs = []
    content = path.read_text("utf-8")
    blocks = re.split(r"\n\s*\n", content)
    time_pattern = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})")

    for block in blocks:
        m = time_pattern.search(block)
        if not m:
            continue
        start = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000
        end = int(m.group(5)) * 3600 + int(m.group(6)) * 60 + int(m.group(7)) + int(m.group(8)) / 1000
        # Text is everything after the timestamp line
        text_lines = block.splitlines()[2:]  # skip sequence number + timestamp
        text = " ".join(line.strip() for line in text_lines if line.strip())
        if text:
            subs.append({"start": start, "end": end, "text": text})

    return subs


async def seed_video(entry: dict, force_update: bool = False) -> bool:
    """Seed a single official video. Returns True if created/updated, False if skipped.

    Args:
        entry: Video entry dict with id, category, title, etc.
        force_update: If True, re-fetch metadata even if video already exists.
    """
    video_id_yt = entry["id"]
    source_url = f"https://www.youtube.com/watch?v={video_id_yt}"
    category = entry.get("category", "all")

    async with async_session() as db:
        # Check if already exists (idempotent)
        result = await db.execute(select(Video).where(Video.source_url == source_url))
        existing = result.scalars().first()
        if existing and not force_update:
            print(f"  [SKIP] Already exists: {existing.title} (id={existing.id})")
            return False
        elif existing and force_update:
            print(f"  [UPDATE] Re-seeding: {existing.title} (id={existing.id})")
            # Delete old subtitles before re-fetching
            from sqlalchemy import delete

            await db.execute(delete(Subtitle).where(Subtitle.video_id == existing.id))
            await db.commit()
            video = existing
            video.status = VideoStatus.processing
        else:
            # New video - create record
            video = None

        # Fetch metadata
        print(f"  [META] Fetching metadata for {video_id_yt}...")
        meta = _fetch_metadata(video_id_yt)
        if not meta:
            print(f"  [FAIL] Skipping {video_id_yt}: metadata fetch failed")
            return False

        # Fetch subtitles
        print("  [SUBS] Fetching subtitles...")
        subs = _fetch_subtitles(video_id_yt)

        # Create video record (only for new videos)
        if video is None:
            video = Video(
                id=str(uuid.uuid4()),
                title=entry.get("title") or meta.get("title", "Untitled"),
                source_url=source_url,
                video_source=VideoSource.imported,
                thumbnail_url=meta.get("thumbnail", f"https://i.ytimg.com/vi/{video_id_yt}/maxresdefault.jpg"),
                duration=meta.get("duration"),
                is_official=True,
                processing_mode="lightweight",
                topic_tags=category,
                status=VideoStatus.processing,
            )
            db.add(video)
            await db.commit()
        else:
            # Update existing video metadata
            video.title = entry.get("title") or meta.get("title", video.title)
            video.thumbnail_url = meta.get("thumbnail", video.thumbnail_url)
            video.duration = meta.get("duration", video.duration)
            video.topic_tags = category
            video.status = VideoStatus.processing
            await db.commit()

        # Insert subtitles if available
        if subs:
            for i, sub in enumerate(subs):
                db.add(
                    Subtitle(
                        video_id=video.id,
                        start_time=sub["start"],
                        end_time=sub["end"],
                        text_en=sub["text"],
                        sentence_index=i,
                    )
                )
            await db.commit()
            video.status = VideoStatus.ready_subtitles
            await db.commit()
            print(f"  [OK] {len(subs)} English subtitles saved")
        else:
            print("  [WARN] No subtitles found -- video will be ready but without subtitles")

        # Mark as ready and publish. This script bypasses the Celery finalize
        # pipeline (it inserts subtitles via yt-dlp directly), so unlike the
        # admin "seed-full" flow — which sets auto_publish=True and lets
        # finalize_video flip is_published on the ready step — we publish
        # here. list_public_videos / recommendation_service / search_service
        # all filter is_published == True, so without this the seeded
        # homepage is empty even though the videos are status=ready.
        video.status = VideoStatus.ready
        video.is_published = True

        # Download thumbnail to local media dir so the server doesn't need
        # to proxy YouTube CDN at runtime (which fails in mainland China).
        ext_thumb = video.thumbnail_url or ""
        if ext_thumb.startswith("http"):
            settings = get_settings()
            media_dir = Path(settings.local_media_path)
            local_path = media_dir / f"{video.id}_thumb.jpg"
            if not local_path.exists():
                if _download_thumbnail(ext_thumb, local_path, video.id):
                    video.thumbnail_url = f"/media/{video.id}_thumb.jpg"

        await db.commit()

        print(f"  [DONE] Seeded: {video.title} (id={video.id}, category={category})")
        return True


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Seed official videos for the SeeWord homepage")
    parser.add_argument("--force", action="store_true", help="Force re-seed existing videos")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be seeded without writing to DB")
    parser.add_argument("--category", type=str, help="Only seed videos from a specific category (ted, interview, etc.)")
    args = parser.parse_args()

    print("=" * 60)
    print("[SEED] Seeding official videos for the SeeWord homepage")
    print("=" * 60)

    # Filter videos by category if specified
    videos_to_seed = OFFICIAL_VIDEOS
    if args.category:
        videos_to_seed = [v for v in videos_to_seed if v.get("category") == args.category]
        print(f"Filtered to category '{args.category}': {len(videos_to_seed)} videos")

    settings = get_settings()
    print(f"Database: {settings.database_url[:30]}...")
    print(f"Proxy: {settings.http_proxy or '(none)'}")
    print(f"Videos to seed: {len(videos_to_seed)}")
    if args.force:
        print("Mode: FORCE UPDATE (will re-seed existing videos)")
    if args.dry_run:
        print("Mode: DRY RUN (no changes to database)")
    print()

    if args.dry_run:
        for i, entry in enumerate(videos_to_seed, 1):
            print(f"[{i}/{len(videos_to_seed)}] Would seed: {entry.get('title', entry['id'])}")
        print("\n[SEED] Dry run complete. No changes made.")
        return

    created = 0
    skipped = 0
    failed = 0

    for i, entry in enumerate(videos_to_seed, 1):
        print(f"[{i}/{len(videos_to_seed)}] {entry.get('title', entry['id'])}")
        try:
            if await seed_video(entry, force_update=args.force):
                created += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"[SEED] Seeding complete: {created} created/updated, {skipped} skipped, {failed} failed")
    print("=" * 60)

    if created > 0:
        print("\nVisit http://localhost:3000/ to see the homepage videos!")


if __name__ == "__main__":
    asyncio.run(main())

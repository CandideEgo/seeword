"""Unified transcription service for SeeWord app.

Uses WhisperX for high-quality transcription with:
- VAD preprocessing (pyannote/silero) to reduce hallucination
- Batched inference for faster transcription
- wav2vec2 forced alignment for precise word-level timestamps
- NLTK Punkt sentence segmentation

Supports:
- Local video files (ffmpeg audio extraction)
- Streaming URLs (yt-dlp pipe → ffmpeg) for admin imports
"""

import asyncio
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import structlog

from gpu_worker.config import get_settings
from gpu_worker.sources import VideoSource

from .audio_extractor import (
    _is_streaming_url,
    download_http_to_temp,
    extract_local_audio,
    extract_streaming_audio,
    get_video_duration,
)
from .chunked_transcription import transcribe_local_chunks
from .exceptions import AudioExtractionError, TranscriptionError, UnsupportedPlatformError
from .formatters import whisperx_segments_to_subtitles

logger = structlog.get_logger()


class TranscriptionService:
    """Unified transcription service for all video sources."""

    def __init__(self):
        self.settings = get_settings()
        # Real audio length in seconds, measured by ffprobe during the last
        # ``_sync_transcribe`` call (None until then / after a failure).
        #
        # Exposed as an attribute rather than folded into the return value so
        # ``_sync_transcribe`` keeps returning the plain subtitle list that
        # callers and test doubles already expect. The cloud's hallucination
        # check needs a duration that is independent of the subtitles it checks;
        # deriving it from the last subtitle made that check a tautology.
        self.last_audio_duration: float | None = None

    async def transcribe(self, source: str, platform: VideoSource) -> list[dict]:
        """Transcribe a video into subtitles.

        Args:
            source: Video URL or local file path.
            platform: VideoSource enum value.

        Returns:
            list[dict]: [{"start": float, "end": float, "text": str}, ...]

        Raises:
            TranscriptionError: If transcription fails.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._sync_transcribe,
            source,
            platform,
        )

    def _sync_transcribe(self, source: str, platform: VideoSource) -> list[dict]:
        """Synchronous transcription core logic using WhisperX."""
        # Create temp directory for audio files
        temp_dir = Path(self.settings.transcription_temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Reset first: a failed run must not report the previous video's length.
        self.last_audio_duration = None
        audio_path = None
        extra_cleanups: list[str] = []
        try:
            # Step 1: Extract audio
            audio_path, extra_cleanups = self._extract_audio(source, platform, temp_dir)
            if not audio_path or not Path(audio_path).exists():
                raise TranscriptionError("Failed to extract audio from video")

            # Step 2: Get duration (also reported to the cloud, see
            # ``last_audio_duration``).
            duration = get_video_duration(audio_path)
            self.last_audio_duration = duration
            logger.info("Audio duration", duration=f"{duration:.1f}s")

            # Step 3: Transcribe + align with WhisperX
            if duration > self.settings.whisper_chunk_duration:
                logger.info(
                    "Video exceeds chunk duration, using chunked transcription",
                    chunk_duration=self.settings.whisper_chunk_duration,
                )
                subs = self._transcribe_chunked_sync(audio_path, duration)
            else:
                subs = self._transcribe_single(audio_path)

            logger.info("Transcription complete", subtitle_count=len(subs))
            return subs

        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
            # Clean up any downloaded source files (OSS/CDN URLs).
            for path in extra_cleanups:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass

    def _extract_audio(self, source: str, platform: VideoSource, temp_dir: Path) -> tuple[str | None, list[str]]:
        """Extract audio based on source type.

        Returns:
            ``(audio_path, extra_cleanups)`` where ``extra_cleanups`` is a list
            of additional temp file paths (e.g. downloaded source media) the
            caller should remove when done.
        """
        audio_path = str(temp_dir / f"audio_{abs(hash(source))}.wav")
        extra_cleanups: list[str] = []

        if platform == VideoSource.local:
            logger.info("Extracting local audio", source=source)
            extract_local_audio(source, audio_path)
            return audio_path, extra_cleanups

        parsed = urlparse(source)
        if parsed.scheme in ("http", "https"):
            # Streaming video hosts (YouTube, Bilibili, ...) → yt-dlp pipe → ffmpeg.
            if _is_streaming_url(source):
                logger.info("Extracting streaming audio", source=source[:80])
                extract_streaming_audio(source, audio_path)
                return audio_path, extra_cleanups
            # Generic HTTP(S) download (OSS signed URL / CDN / direct media)
            # → local temp file → ffmpeg. Used by the remote GPU worker for
            # locally-uploaded videos whose raw file is staged on OSS.
            downloaded = download_http_to_temp(source, temp_dir)
            extra_cleanups.append(downloaded)
            extract_local_audio(downloaded, audio_path)
            return audio_path, extra_cleanups

        # Fallback: try as local file
        if Path(source).exists():
            logger.info("Treating as local file", source=source)
            extract_local_audio(source, audio_path)
            return audio_path, extra_cleanups

        raise UnsupportedPlatformError(f"Cannot extract audio from: {source}")

    def _transcribe_single(self, audio_path: str) -> list[dict]:
        """Transcribe a single audio file and format as subtitles.

        Dispatches to the configured engine (WhisperX by default, with
        automatic faster-whisper fallback on WhisperX failure).

        Returns:
            list[dict]: Subtitle dicts with sentence-level segmentation.
        """
        from .whisper_model import transcribe_audio

        logger.info("Transcribing audio", audio_path=audio_path, engine=self.settings.whisper_engine)
        segments = transcribe_audio(audio_path)
        logger.info("Transcription complete", segment_count=len(segments))
        return whisperx_segments_to_subtitles(segments)

    def _transcribe_chunked_sync(self, audio_path: str, duration: float) -> list[dict]:
        """Run chunked transcription synchronously.

        Since chunked transcription is async, we need to run it in a new event loop.
        """
        import asyncio

        async def _run():
            return await transcribe_local_chunks(audio_path, duration)

        try:
            return asyncio.run(_run())
        except RuntimeError:
            # If there's already a running event loop (e.g., in Celery)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(transcribe_local_chunks(audio_path, duration))
            finally:
                loop.close()


# Backwards-compatible alias for direct import
async def transcribe_video(source: str, platform: VideoSource) -> list[dict]:
    """Convenience function to transcribe a video.

    Args:
        source: Video URL or local file path.
        platform: VideoSource enum value.

    Returns:
        list[dict]: Subtitle dicts.
    """
    service = TranscriptionService()
    return await service.transcribe(source, platform)

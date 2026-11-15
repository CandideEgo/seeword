"""Automated YouTube cookie refresh via playwright-cli --persistent.

Opens or reuses a persistent browser session, waits for YouTube login,
exports cookies to Netscape format, and verifies them with yt-dlp.

Usage:
    # Full refresh + verify (default)
    python scripts/refresh_youtube_cookies.py

    # Skip yt-dlp verification
    python scripts/refresh_youtube_cookies.py --no-verify

    # Custom timeout and output path
    python scripts/refresh_youtube_cookies.py --timeout 180 --output ./my_cookies.txt

    # Quiet mode (for cron / CI)
    python scripts/refresh_youtube_cookies.py --quiet

Exit codes: 0 = success, 1 = failure.
"""

import argparse
import logging
import shutil
import sys
import time
from pathlib import Path

# Ensure backend/ is on sys.path so `from scripts.*` works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Reuse helpers from get_youtube_cookies.py
# ---------------------------------------------------------------------------
from scripts.get_youtube_cookies import (
    convert_to_netscape,
    is_browser_open,
    is_youtube_logged_in,
    open_youtube_persistent,
    save_session_state,
)

logger = logging.getLogger("refresh_cookies")

DEFAULT_OUTPUT = "./youtube_cookies.txt"
DEFAULT_VERIFY_URL = "https://www.youtube.com/watch?v=8jPQjjsBbIc"
DEFAULT_TIMEOUT = 120
POLL_INTERVAL = 3


def _check_playwright_cli() -> bool:
    """Verify playwright-cli is available on PATH."""
    if shutil.which("playwright-cli"):
        return True
    logger.error(
        "playwright-cli not found on PATH. Install: pip install -r requirements-dev.txt && playwright install chromium"
    )
    return False


def _probe_with_ytdlp(cookies_path: str, url: str) -> bool:
    """Probe a URL with yt-dlp using the given cookies file.

    Returns True if yt-dlp can extract metadata (no download).
    """
    try:
        import yt_dlp
    except ImportError:
        logger.warning("yt-dlp not installed — skipping probe")
        return True  # can't verify, assume ok

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cookiefile": cookies_path,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=False)
        return True
    except Exception as e:
        logger.warning("yt-dlp probe failed: %s", str(e)[:200])
        return False


def refresh_cookies(
    output_path: str = DEFAULT_OUTPUT,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    verify_url: str | None = DEFAULT_VERIFY_URL,
) -> bool:
    """Full cookie refresh cycle: open browser → wait login → export → verify.

    Returns True on success.
    """
    # Step 1: Ensure playwright-cli is available
    if not _check_playwright_cli():
        return False

    # Step 2: Open or reuse persistent browser
    if is_browser_open():
        logger.info("Persistent browser session already open")
    else:
        logger.info("Opening YouTube with persistent profile...")
        open_youtube_persistent()
        time.sleep(3)  # give browser time to load

    # Step 3: Poll for LOGIN_INFO cookie (wait for manual login if needed)
    logger.info("Waiting for YouTube login (up to %ds)...", timeout)
    deadline = time.monotonic() + timeout
    logged_in = False

    while time.monotonic() < deadline:
        if is_youtube_logged_in():
            logged_in = True
            break
        remaining = int(deadline - time.monotonic())
        if remaining > 0 and remaining % 15 == 0:
            logger.info("  ...still waiting (%ds remaining)", remaining)
        time.sleep(POLL_INTERVAL)

    if not logged_in:
        logger.error("❌ Timeout — not logged in to YouTube. Please log in manually and re-run.")
        return False

    logger.info("LOGIN_INFO cookie found — logged in")

    # Step 4: Export session state → Netscape cookies
    logger.info("Saving browser session state...")
    state_path = save_session_state()
    success = convert_to_netscape(state_path, output_path)

    # Clean up temp state file
    try:
        Path(state_path).unlink(missing_ok=True)
    except OSError:
        pass

    if not success:
        logger.error("❌ Failed to export cookies")
        return False

    # Step 5: Verify with yt-dlp (optional)
    if verify_url:
        logger.info("Probing yt-dlp with %s ...", verify_url)
        if _probe_with_ytdlp(output_path, verify_url):
            logger.info("yt-dlp probe OK — cookies are valid ✅")
        else:
            logger.warning("yt-dlp probe FAILED — cookies may not work for all videos")
            logger.info("  Cookies were exported successfully. The probe video may be restricted.")
            logger.info("  Try a different video with --verify URL, or use --no-verify to skip.")
            # Don't fail entirely — cookies are exported, just the probe video failed
    else:
        logger.info("Skipping yt-dlp verification (--no-verify)")

    logger.info("✅ Cookie refresh complete → %s", output_path)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Automated YouTube cookie refresh via playwright-cli --persistent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full refresh + verify (default)
  python scripts/refresh_youtube_cookies.py

  # Skip yt-dlp verification
  python scripts/refresh_youtube_cookies.py --no-verify

  # Custom timeout and output path
  python scripts/refresh_youtube_cookies.py --timeout 180 --output ./my_cookies.txt

  # Quiet mode (for cron / CI)
  python scripts/refresh_youtube_cookies.py --quiet
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT,
        help=f"Output cookies file path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Seconds to wait for manual login (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--verify",
        default=DEFAULT_VERIFY_URL,
        help="URL to probe with yt-dlp after export (default: TED-Ed short video)",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip yt-dlp verification after export",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode — only print errors and final result",
    )

    args = parser.parse_args()

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    verify_url = None if args.no_verify else args.verify

    success = refresh_cookies(
        output_path=args.output,
        timeout=args.timeout,
        verify_url=verify_url,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

"""Run existing mobile layout tests against a disposable local API/database.

The frontend dev server must already be listening on localhost:3000. No SMS,
real account, project database, worker, or external media is used.
"""

import argparse
import asyncio
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_watch_postgres import provision


async def seed(media: Path) -> str:
    from app import models  # noqa: F401 - register all ORM tables before create_all.
    from app.core.config import get_settings
    from app.core.database import Base, get_async_session_maker, get_engine
    from app.core.security import create_token
    from app.models.subtitle import Subtitle
    from app.models.user import User
    from app.models.video import Video, VideoStatus

    get_settings.cache_clear()
    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    video_id = str(uuid.uuid4())
    fixture = Path(__file__).resolve().parents[2] / "frontend/e2e/fixtures/watch-clock.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-stream_loop",
            "8",
            "-i",
            str(fixture),
            "-t",
            "180",
            "-c",
            "copy",
            str(media / f"{video_id}.mp4"),
        ],
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    async with get_async_session_maker()() as db:
        user = User(name="Disposable mobile test", onboarding_completed=True, level="B1")
        video = Video(
            id=video_id,
            title="Local mobile layout fixture",
            source_url="https://example.com/test",
            video_source="imported",
            status=VideoStatus.ready,
            is_official=True,
            is_published=True,
            is_demo=True,
            duration=180,
            video_url_480p=f"/media/{video_id}.mp4",
        )
        db.add_all([user, video])
        await db.flush()
        for index in range(15):
            db.add(
                Subtitle(
                    video_id=video_id,
                    sentence_index=index,
                    start_time=index * 12,
                    end_time=(index + 1) * 12,
                    text_en="We can understand the whole sentence when we listen carefully to the original words and pay attention to the speaker, even when the sentence is longer than the available space on a small screen.",
                    text_zh="仔细听原声并关注说话者，即使句子比手机屏幕上的可用空间更长，我们也可以逐步理解完整的意思。",
                )
            )
        await db.commit()
        token = create_token(user.id)
    await engine.dispose()
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", required=True)
    parser.add_argument("--grep", help="Optional Playwright title filter")
    args = parser.parse_args()
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            raise RuntimeError("Port 8000 is occupied; do not replace an existing API")
    backend = Path(__file__).resolve().parents[1]
    frontend = backend.parent / "frontend"
    original_url = os.environ.get("DATABASE_URL")
    name = "seeword_watch_test_" + uuid.uuid4().hex[:12]
    os.environ["JWT_SECRET"] = uuid.uuid4().hex + uuid.uuid4().hex
    url = asyncio.run(provision(name))
    print(f"Disposable database: {name}", flush=True)
    server = None
    try:
        with tempfile.TemporaryDirectory(prefix="seeword-watch-mobile-") as folder:
            media = Path(folder)
            os.environ["DATABASE_URL"] = url
            os.environ["LOCAL_MEDIA_PATH"] = str(media)
            os.environ["ENV"] = "testing"
            os.environ["PUNCTUATION_MODEL_DISABLED"] = "1"
            token = asyncio.run(seed(media))
            log_path = Path(tempfile.gettempdir()) / "seeword-watch-mobile-api.log"
            with log_path.open("w", encoding="utf-8") as log:
                server = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--port",
                        "8000",
                        # Same reason as playwright.config.ts / CI: uvicorn's 5s
                        # keep-alive default closes connections the dev proxy is
                        # still reusing → ECONNRESET surfaces as a proxy 500.
                        "--timeout-keep-alive",
                        "120",
                    ],
                    cwd=backend,
                    stdout=log,
                    stderr=log,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                for _ in range(30):
                    if server.poll() is not None:
                        raise RuntimeError(f"Disposable API exited; inspect {log_path}")
                    try:
                        with urllib.request.urlopen(
                            "http://localhost:8000/api/v1/videos/public?page_size=1", timeout=1
                        ) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(1)
                else:
                    raise RuntimeError("Disposable API did not become ready")
                child_env = {**os.environ, "CI": "1", "DESIGN_E2E_TOKEN": token}
                tests = [
                    path.relative_to(frontend).as_posix()
                    for path in sorted((frontend / "e2e").glob("mobile-*.spec.ts"))
                ]
                command = [
                    args.node,
                    "node_modules/@playwright/test/cli.js",
                    "test",
                    *tests,
                    "--project=chromium",
                    "--workers=1",
                    "--retries=0",
                    "--reporter=line",
                    "--output=test-results/mobile-final",
                ]
                if args.grep:
                    command += ["--grep", args.grep]
                result = subprocess.run(
                    command,
                    cwd=frontend,
                    env=child_env,
                )
                return result.returncode
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=15)
        if original_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_url
        # provision uses the original cached local credentials; only this UUID DB is dropped.
        asyncio.run(provision(name, drop=True))


if __name__ == "__main__":
    raise SystemExit(main())

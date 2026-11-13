"""GPU transcription callback delivery (BE-11).

The GPU worker is the only component that finishes a transcription and then
has to POST the result back. Two defects this file pins:

* 429 (and 408/425) used to be treated as a permanent 4xx, so a finished
  transcription was silently dropped when the callback endpoint rate-limited
  the worker.
* ``transcribe_video_gpu`` ignored the callback's boolean result and returned
  success, leaving the cloud video stuck in ``processing`` until the watchdog.

The Celery task is invoked through its raw function (``.run.__func__``) with a
fake ``self`` so the retry branch is observable without a broker.
"""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

from gpu_worker import tasks as video_processing
from gpu_worker.tasks import _post_transcription_callback, transcribe_video_gpu


class _Resp:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.text = f"status={status_code}"


class _FakeClient:
    responses: ClassVar[list[_Resp]] = []
    calls: ClassVar[list[dict[str, Any]]] = []

    def __init__(self, timeout: float | None = None) -> None:
        self.timeout = timeout

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def post(self, url: str, json: dict | None = None, headers: dict | None = None) -> _Resp:
        _FakeClient.calls.append({"url": url, "json": json, "headers": headers})
        return _FakeClient.responses.pop(0)


def _callback_settings(monkeypatch, *, max_retries: int = 2) -> None:
    settings = video_processing.get_settings()
    monkeypatch.setattr(settings, "transcription_callback_url", "http://cloud/internal/callback", raising=False)
    monkeypatch.setattr(settings, "transcription_callback_secret", "test-secret", raising=False)
    monkeypatch.setattr(settings, "transcription_callback_max_retries", max_retries, raising=False)
    monkeypatch.setattr(settings, "transcription_callback_timeout", 1.0, raising=False)
    monkeypatch.setattr(video_processing.time, "sleep", lambda _s: None)


@pytest.fixture
def fake_httpx(monkeypatch):
    """Patch ``httpx.Client`` as imported inside the callback function."""
    import httpx

    _FakeClient.responses = []
    _FakeClient.calls = []
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    return _FakeClient


class TestCallbackDelivery:
    def test_rate_limited_callback_is_retried(self, monkeypatch, fake_httpx):
        _callback_settings(monkeypatch)
        fake_httpx.responses = [_Resp(429), _Resp(200)]

        assert _post_transcription_callback("vid-1", status="ok", segments=[{"start": 0, "end": 1, "text": "Hi"}])
        assert [c["json"]["video_id"] for c in fake_httpx.calls] == ["vid-1", "vid-1"]

    def test_permanent_4xx_is_not_retried(self, monkeypatch, fake_httpx):
        _callback_settings(monkeypatch)
        fake_httpx.responses = [_Resp(401)]

        assert not _post_transcription_callback("vid-2", status="ok", segments=[])
        assert len(fake_httpx.calls) == 1

    def test_exhausted_retries_returns_false(self, monkeypatch, fake_httpx):
        _callback_settings(monkeypatch, max_retries=2)
        fake_httpx.responses = [_Resp(503), _Resp(503), _Resp(503)]

        assert not _post_transcription_callback("vid-3", status="ok", segments=[])
        assert len(fake_httpx.calls) == 3

    def test_payload_reports_measured_audio_duration(self, monkeypatch, fake_httpx):
        """The cloud's duration sanity check needs the REAL audio length.

        It compares the measured length against the subtitles; when the payload
        carried ``segments[-1].end`` instead, `last_end > duration * 1.5` could
        never fire and the check passed on every input.
        """
        _callback_settings(monkeypatch)
        fake_httpx.responses = [_Resp(200)]
        segments = [{"start": 0, "end": 1, "text": "Hi"}]

        assert _post_transcription_callback("vid-4", status="ok", segments=segments, audio_duration=12.5)
        assert fake_httpx.calls[0]["json"]["audio_duration"] == 12.5

        # Without a measured duration the field stays null — never the last
        # subtitle's end, which would re-introduce the tautology.
        fake_httpx.responses = [_Resp(200)]
        assert _post_transcription_callback("vid-5", status="ok", segments=segments)
        assert fake_httpx.calls[1]["json"]["audio_duration"] is None


class _RetryError(Exception):
    pass


class _FakeTaskSelf:
    max_retries = 3
    request = SimpleNamespace(retries=0)

    def __init__(self) -> None:
        self.retries: list[tuple[Exception, int]] = []

    def retry(self, exc: Exception, countdown: int) -> None:
        self.retries.append((exc, countdown))
        raise _RetryError


class _FakeTranscriptionService:
    def __init__(self) -> None:
        self.calls = 0

    def _sync_transcribe(self, source: str, platform: object) -> list[dict]:
        self.calls += 1
        return [{"start": 0.0, "end": 1.0, "text": "Hello"}]


@pytest.fixture
def fake_transcription(monkeypatch):
    service = _FakeTranscriptionService()
    # Function-local import: patch the class on its home module.
    module = types.ModuleType("gpu_worker.transcription")
    module.TranscriptionService = lambda: service  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "gpu_worker.transcription", module)
    return service


class TestGpuTaskRetry:
    def test_failed_delivery_retries_the_task(self, monkeypatch, fake_transcription):
        monkeypatch.setattr(video_processing, "_post_transcription_callback", lambda *a, **k: False)
        fake_self = _FakeTaskSelf()

        with pytest.raises(_RetryError):
            transcribe_video_gpu.run.__func__(fake_self, "vid-4", "https://example.com/a.mp4", "local")

        assert fake_transcription.calls == 1
        assert len(fake_self.retries) == 1
        assert isinstance(fake_self.retries[0][0], RuntimeError)

    def test_successful_delivery_does_not_retry(self, monkeypatch, fake_transcription):
        monkeypatch.setattr(video_processing, "_post_transcription_callback", lambda *a, **k: True)
        fake_self = _FakeTaskSelf()

        transcribe_video_gpu.run.__func__(fake_self, "vid-5", "https://example.com/b.mp4", "local")

        assert fake_transcription.calls == 1
        assert fake_self.retries == []

    def test_final_delivery_failure_sends_an_alert(self, monkeypatch, fake_transcription):
        monkeypatch.setattr(video_processing, "_post_transcription_callback", lambda *a, **k: False)
        alerts: list[TitleAndMessage] = []
        monkeypatch.setattr(
            video_processing, "_send_alert_sync", lambda title, message, **k: alerts.append((title, message))
        )
        fake_self = _FakeTaskSelf()
        fake_self.request = SimpleNamespace(retries=fake_self.max_retries)

        with pytest.raises(_RetryError):
            transcribe_video_gpu.run.__func__(fake_self, "vid-6", "https://example.com/c.mp4", "local")

        assert len(alerts) == 1
        assert "vid-6" in alerts[0][1]

    def test_final_transcription_failure_sends_an_alert(self, monkeypatch, fake_transcription):
        def _boom(_source: str, _platform: object) -> list[dict]:
            raise RuntimeError("whisper crashed")

        monkeypatch.setattr(fake_transcription, "_sync_transcribe", _boom)
        callbacks: list[tuple] = []
        monkeypatch.setattr(
            video_processing,
            "_post_transcription_callback",
            lambda *a, **k: callbacks.append((a, k)) or True,
        )
        alerts: list[TitleAndMessage] = []
        monkeypatch.setattr(
            video_processing, "_send_alert_sync", lambda title, message, **k: alerts.append((title, message))
        )
        fake_self = _FakeTaskSelf()
        fake_self.request = SimpleNamespace(retries=fake_self.max_retries)

        with pytest.raises(RuntimeError, match="whisper crashed"):
            transcribe_video_gpu.run.__func__(fake_self, "vid-7", "https://example.com/d.mp4", "local")

        assert callbacks and callbacks[0][1]["status"] == "error"
        assert len(alerts) == 1
        assert "vid-7" in alerts[0][1]


TitleAndMessage = tuple[str, str]

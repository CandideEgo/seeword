"""无模型能力关闭必须先于网络、派发、业务写入。仅内存 DB，不使用业务库。"""

from unittest.mock import AsyncMock, Mock

import pytest

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError
from app.services import ai_service, home_content_service, pipeline_dispatch, teaching_gateway, video_seed_service
from app.services.llm_provider import resolve_provider
from app.services.translation import TranslationService


@pytest.fixture
def disabled(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "llm_enabled", False)
    monkeypatch.setattr(settings, "content_production_enabled", False)
    return settings


async def test_model_exits_reject_even_with_cached_clients(disabled):
    client = Mock()
    client.chat.completions.create = AsyncMock()
    service = ai_service.AIService()
    service.client = client
    service._engine_clients["qwen"] = (client, "qwen")
    with pytest.raises(ai_service.AIServiceError, match="已关闭"):
        await service._chat("system", "user")
    with pytest.raises(ai_service.AIServiceError, match="已关闭"):
        service._get_engine_client("qwen")
    with pytest.raises(ai_service.AIServiceError, match="已关闭"):
        await service._generate_word_notes_one_batch([], "global", "global", client, "model")
    with pytest.raises(ai_service.AIServiceError, match="已关闭"):
        await service.generate_word_notes_bulk([{"word": "test"}], "global")
    client.chat.completions.create.assert_not_called()
    assert resolve_provider(disabled) is None


def test_translation_and_gateway_exits_reject(disabled):
    with pytest.raises(ServiceUnavailableError, match="已关闭"):
        TranslationService()
    with pytest.raises(ServiceUnavailableError, match="已关闭"):
        TranslationService.resolve_engine_client("qwen")
    with pytest.raises(ServiceUnavailableError, match="已关闭"):
        teaching_gateway.require_gateway()


@pytest.mark.parametrize(
    "action", ["seed", "start", "recover", "retry", "retranslate", "home_claim", "home_enqueue", "outbox"]
)
async def test_disabled_creation_does_not_touch_database(disabled, action):
    db = Mock()
    calls = {
        "seed": lambda: video_seed_service.seed_video(db, "https://example.com/test"),
        "start": lambda: video_seed_service.start_processing(db, "video"),
        "recover": lambda: video_seed_service.recover_processing(db, "video"),
        "retry": lambda: video_seed_service.retry_video(db, "video"),
        "retranslate": lambda: video_seed_service.retranslate_video(db, "video"),
        "home_claim": lambda: home_content_service.claim_generation(db, "video", "admin"),
        "home_enqueue": lambda: home_content_service.enqueue_generation(db, Mock()),
        "outbox": lambda: pipeline_dispatch.enqueue(db, video_id="video", task_name="task", args=[]),
    }
    with pytest.raises(ServiceUnavailableError, match="已关闭"):
        await calls[action]()
    assert db.mock_calls == []


async def test_full_seed_cookie_probe_is_gated_before_network(disabled, monkeypatch):
    from app.api.v1.videos import _require_valid_cookies
    from app.services import youtube_cookies_service

    probe = AsyncMock()
    monkeypatch.setattr(youtube_cookies_service, "ensure_cookies", probe)
    with pytest.raises(ServiceUnavailableError, match="已关闭"):
        await _require_valid_cookies("https://www.youtube.com/watch?v=abcdefghijk")
    probe.assert_not_called()


async def test_pending_outbox_is_preserved_while_disabled(disabled):
    db = Mock()
    row = Mock(task_name=pipeline_dispatch.FINALIZE_VIDEO_TASK)
    assert await pipeline_dispatch._attempt(db, row) is False
    assert db.mock_calls == []
    assert row.mock_calls == []


def test_already_queued_pipeline_cannot_execute(disabled):
    from app.tasks.video_processing import finalize_video, localize_video, process_video

    for task in (process_video, finalize_video, localize_video):
        with pytest.raises(ServiceUnavailableError, match="已关闭"):
            task.run("synthetic-video")


async def test_callback_rejects_before_database(disabled):
    from app.api.v1.internal import transcription_callback
    from app.schemas.video import TranscriptionCallbackRequest

    db = Mock()
    with pytest.raises(ServiceUnavailableError, match="已关闭"):
        await transcription_callback(
            request=Mock(),
            payload=TranscriptionCallbackRequest(video_id="v", status="ok", subtitles=[]),
            x_callback_secret="even-a-valid-leftover-secret",
            db=db,
        )
    assert db.mock_calls == []


async def test_disabled_daily_download_retry_never_probes(disabled, monkeypatch):
    from app.services import youtube_cookies_service
    from app.tasks.video_processing import _run_retry_failed_downloads

    probe = AsyncMock()
    monkeypatch.setattr(youtube_cookies_service, "ensure_cookies_for_pipeline", probe)
    await _run_retry_failed_downloads()
    probe.assert_not_called()


def test_real_redis_transport_accepts_the_pinned_client_without_network():
    # Constructing the transport client is the actual compatibility guard that
    # a fresh worker hits; unit mocks must not hide this late startup failure.
    from types import SimpleNamespace

    import redis
    from kombu.transport.redis import Channel

    assert Channel._get_client(SimpleNamespace(global_keyprefix="")) is redis.Redis


def test_smoke_synthetic_pack_obeys_the_real_contract():
    import json

    from scripts.smoke_selfhost import synthetic_pack
    from slcs import load_pack

    pack = load_pack(json.dumps(synthetic_pack(), ensure_ascii=False).encode("utf-8"))
    assert pack.lesson_id == "selfhost-smoke"
    assert pack.segments[0].text == "Read safely."


@pytest.mark.parametrize(
    "field,value",
    [
        ("env", "testing"),
        ("llm_enabled", True),
        ("content_production_enabled", True),
        ("sms_dev_fake_enabled", True),
        ("database_url", "postgresql+asyncpg://u:p@db/business"),
        ("database_url", "postgresql+asyncpg://u:p@remote/selfhost_smoke_012345abcdef"),
    ],
)
def test_smoke_refuses_nonisolated_targets(disabled, monkeypatch, field, value):
    from scripts.smoke_selfhost import _ensure_smoke

    monkeypatch.setattr(disabled, "env", "production")
    monkeypatch.setattr(disabled, "sms_dev_fake_enabled", False)
    monkeypatch.setattr(disabled, "database_url", "postgresql+asyncpg://u:p@db/selfhost_smoke_012345abcdef")
    monkeypatch.setenv("SELFHOST_SMOKE_ID", "selfhost_smoke_012345abcdef")
    _ensure_smoke()
    monkeypatch.setattr(disabled, field, value)
    with pytest.raises(RuntimeError, match="Refusing"):
        _ensure_smoke()


def test_smoke_does_not_inherit_official_environment(monkeypatch):
    from scripts.smoke_selfhost import _docker_environment

    for key in ("COMPOSE_FILE", "DB_PASSWORD", "OPENAI_API_KEY", "DOCKER_HOST", "LLM_ENABLED"):
        monkeypatch.setenv(key, "must-not-leak")
    child = _docker_environment()
    assert not ({"COMPOSE_FILE", "DB_PASSWORD", "OPENAI_API_KEY", "DOCKER_HOST", "LLM_ENABLED"} & child.keys())


@pytest.mark.parametrize(
    "actual,expected,exit_code",
    [
        ({"head"}, {"head"}, 0),
        (set(), {"head"}, 1),
        ({"old"}, {"head"}, 1),
        ({"head", "unexpected"}, {"head"}, 1),
        (set(), set(), 1),
    ],
)
def test_release_gate_compares_exact_heads(monkeypatch, actual, expected, exit_code):
    from scripts import check_schema_revision

    check = AsyncMock(return_value=(actual, expected))
    monkeypatch.setattr(check_schema_revision, "check_revision", check)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@db/isolated")
    assert check_schema_revision.main() == exit_code
    check.assert_awaited_once_with("postgresql+asyncpg://u:p@db/isolated")


def test_release_gate_refuses_implicit_db_and_hides_driver_secrets(monkeypatch, capsys):
    from scripts import check_schema_revision

    check = AsyncMock(side_effect=RuntimeError("driver echoed secret-password"))
    monkeypatch.setattr(check_schema_revision, "check_revision", check)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert check_schema_revision.main() == 1
    check.assert_not_called()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:secret-password@db/isolated")
    assert check_schema_revision.main() == 1
    assert "secret-password" not in capsys.readouterr().out

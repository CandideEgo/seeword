"""Regression tests for the ``ENV`` guard in ``Settings.model_post_init``.

An unrecognized ``ENV`` used to match neither the development defaults nor the
production guards, so the app booted with an empty ``jwt_secret`` (JWTs signed
with an empty key, i.e. forgeable) and no guard at all. These tests pin the
fail-closed behavior: unknown values refuse to start, and the non-development
guard cannot be skipped by any accepted value.
"""

import pytest

from app.core.config import Settings

_STRONG_SECRET = "x" * 32


@pytest.fixture(autouse=True)
def _clear_sms_fake_env(monkeypatch):
    """conftest enables the dev SMS fake suite-wide; these tests assert the
    production guards, so the opt-in must not leak in from the environment."""
    monkeypatch.delenv("SMS_DEV_FAKE_ENABLED", raising=False)


def _settings(**overrides) -> Settings:
    """Build ``Settings`` from the explicit kwargs only.

    ``_env_file=None`` disables the repo's ``.env`` dotenv source so the
    assertions do not depend on the developer's local file. ``os.environ`` still
    applies — tests that assert a value is *missing* must clear it themselves
    (see ``test_production_rejects_defaulted_redis_url``).
    """
    return Settings(_env_file=None, **overrides)


class TestEnvValueGuard:
    def test_unknown_env_refuses_to_start(self):
        with pytest.raises(RuntimeError, match="ENV"):
            _settings(env="staging")

    def test_empty_env_refuses_to_start(self):
        with pytest.raises(RuntimeError, match="ENV"):
            _settings(env="")

    def test_case_variant_is_normalized(self):
        """A casing slip must not skip every downstream ``env == "production"`` check."""
        s = _settings(
            env="Production",
            jwt_secret=_STRONG_SECRET,
            database_url="postgresql+asyncpg://u:p@localhost/db",
            redis_url="redis://localhost:6379/0",
            openai_api_key="k",
            transcription_callback_secret="c",
        )
        assert s.env == "production"

    def test_prod_alias_is_normalized(self):
        """``prod`` is accepted because payment_provider already treats it as production."""
        s = _settings(
            env="prod",
            jwt_secret=_STRONG_SECRET,
            database_url="postgresql+asyncpg://u:p@localhost/db",
            redis_url="redis://localhost:6379/0",
            openai_api_key="k",
            transcription_callback_secret="c",
        )
        assert s.env == "production"


class TestSecretGuards:
    def test_production_rejects_empty_jwt_secret(self):
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            _settings(env="production", jwt_secret="", database_url="postgresql+asyncpg://u:p@localhost/db")

    def test_production_rejects_empty_database_url(self):
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            _settings(env="production", jwt_secret=_STRONG_SECRET, database_url="")

    def test_production_rejects_sms_dev_fake(self):
        """The fixed code '1234' must never be enabled on a production box."""
        with pytest.raises(RuntimeError, match="SMS_DEV_FAKE_ENABLED"):
            _settings(
                env="production",
                jwt_secret=_STRONG_SECRET,
                database_url="postgresql+asyncpg://u:p@localhost/db",
                sms_dev_fake_enabled=True,
            )

    def test_production_rejects_missing_transcription_callback_secret(self):
        with pytest.raises(RuntimeError, match="TRANSCRIPTION_CALLBACK_SECRET"):
            _settings(
                env="production",
                jwt_secret=_STRONG_SECRET,
                database_url="postgresql+asyncpg://u:p@localhost/db",
                redis_url="redis://localhost:6379/0",
                openai_api_key="k",
            )

    def test_production_rejects_defaulted_redis_url(self, monkeypatch):
        """``REDIS_URL`` has a working localhost default, so production must set it explicitly.

        The guard fires when ``redis_url`` was never *set* (``model_fields_set``),
        and an environment variable counts as set — so CI's ``REDIS_URL`` for the
        rest of the suite would satisfy it silently. Clear it for this test.
        """
        monkeypatch.delenv("REDIS_URL", raising=False)
        with pytest.raises(RuntimeError, match="REDIS_URL"):
            _settings(
                env="production",
                jwt_secret=_STRONG_SECRET,
                database_url="postgresql+asyncpg://u:p@localhost/db",
                openai_api_key="k",
                transcription_callback_secret="c",
            )

    def test_production_accepts_commandcode_key_without_openai_key(self):
        """生产可以只用 Command Code 供应商：守卫是「有 LLM key」，不是「有 OpenAI key」。"""
        s = _settings(
            env="production",
            jwt_secret=_STRONG_SECRET,
            database_url="postgresql+asyncpg://u:p@localhost/db",
            redis_url="redis://localhost:6379/0",
            openai_api_key="",
            commandcode_api_key="cc-key",
            transcription_callback_secret="c",
        )
        assert s.commandcode_api_key == "cc-key"

    def test_production_rejects_both_llm_keys_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("COMMANDCODE_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="COMMANDCODE_API_KEY"):
            _settings(
                env="production",
                jwt_secret=_STRONG_SECRET,
                database_url="postgresql+asyncpg://u:p@localhost/db",
                redis_url="redis://localhost:6379/0",
                openai_api_key="",
                commandcode_api_key="",
                transcription_callback_secret="c",
            )

    def test_testing_rejects_empty_jwt_secret(self):
        """``ENV=testing`` must not be a way around the empty-secret guard."""
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            _settings(env="testing", jwt_secret="", database_url="postgresql+asyncpg://u:p@localhost/db")

    def test_testing_rejects_empty_database_url(self):
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            _settings(env="testing", jwt_secret=_STRONG_SECRET, database_url="")

    def test_development_keeps_the_local_defaults(self):
        s = _settings(env="development", jwt_secret="", database_url="")
        assert s.jwt_secret == "dev_secret_change_in_production"
        assert s.database_url == "postgresql+asyncpg://seeword:seeword_dev@localhost:5432/seeword"

    def test_development_keeps_explicit_values(self):
        s = _settings(env="development", jwt_secret="mine", database_url="postgresql+asyncpg://u:p@db/x")
        assert (s.jwt_secret, s.database_url) == ("mine", "postgresql+asyncpg://u:p@db/x")


class TestJwtSecretStrength:
    """A non-empty secret is not enough: short HS256 keys are brute-forceable.

    Losing this guard means anyone who guesses ``JWT_SECRET`` can mint an access
    token for any ``sub`` (admins included), so both guards are pinned.
    """

    @staticmethod
    def _base() -> dict:
        return {
            "database_url": "postgresql+asyncpg://u:p@db/x",
            "redis_url": "redis://localhost:6379/0",
            "openai_api_key": "k",
            "transcription_callback_secret": "c",
        }

    def test_production_rejects_short_jwt_secret(self):
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            _settings(env="production", jwt_secret="x", **self._base())

    def test_testing_rejects_short_jwt_secret(self):
        """ENV=testing must not become the weak-secret loophole either."""
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            _settings(
                env="testing",
                jwt_secret="short",
                database_url="postgresql+asyncpg://u:p@db/x",
            )

    def test_production_rejects_development_default_secret(self):
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            _settings(env="production", jwt_secret="dev_secret_change_in_production", **self._base())

    def test_strong_secret_is_accepted(self):
        s = _settings(env="production", jwt_secret="y" * 32, **self._base())
        assert s.jwt_secret == "y" * 32

    def test_algorithm_is_normalized_to_uppercase(self):
        s = _settings(env="production", jwt_secret="y" * 32, jwt_algorithm="hs256", **self._base())
        assert s.jwt_algorithm == "HS256"

    def test_unsupported_algorithm_is_rejected(self):
        for algorithm in ("none", "RS256", ""):
            with pytest.raises(RuntimeError, match="JWT_ALGORITHM"):
                _settings(env="development", jwt_algorithm=algorithm)


class TestStubPaymentGuard:
    """The WeChat/Alipay callbacks are stubs; production must not boot with them."""

    def test_production_rejects_enabled_legacy_payments(self):
        with pytest.raises(RuntimeError, match="PAYMENTS_ENABLED"):
            _settings(
                env="production",
                jwt_secret="y" * 32,
                database_url="postgresql+asyncpg://u:p@db/x",
                redis_url="redis://localhost:6379/0",
                openai_api_key="k",
                transcription_callback_secret="c",
                payments_enabled=True,
            )


class TestPaymentSignatureDefault:
    """审计 H12：验签必须默认 fail-closed，dev 旁路只能显式开启。"""

    def test_verify_signature_defaults_on(self):
        # production 无旁路路径（_verify_* 只看 development 分支），无需构造。
        for env in ("development", "testing"):
            assert _settings(env=env).payment_verify_signature is True, env

    def test_dev_bypass_requires_explicit_opt_out(self, monkeypatch):
        """默认下无 sign 的回调走验签并失败；显式 False 才旁路（带 warning）。"""
        from app.services import alipay_payment

        monkeypatch.setattr(alipay_payment.settings, "env", "development")
        monkeypatch.setattr(alipay_payment.settings, "payment_verify_signature", True)
        assert alipay_payment._verify_alipay_signature({}) is False

        monkeypatch.setattr(alipay_payment.settings, "payment_verify_signature", False)
        assert alipay_payment._verify_alipay_signature({}) is True


class TestV2FeatureGuards:
    """V2 switches fail closed at boot; a half-configured capability never starts."""

    def test_streaming_requires_dialogue(self):
        with pytest.raises(RuntimeError, match="TEACHING_STREAMING_ENABLED"):
            _settings(env="development", teaching_streaming_enabled=True, teaching_dialogue_enabled=False)

    def test_dialogue_requires_runs(self):
        with pytest.raises(RuntimeError, match="TEACHING_DIALOGUE_ENABLED"):
            _settings(env="development", teaching_dialogue_enabled=True, teaching_runs_enabled=False)

    def test_runs_require_verified_gateway(self):
        with pytest.raises(RuntimeError, match="verified gateway"):
            _settings(env="development", teaching_runs_enabled=True, llm_gateway_governance_verified=False)

    def test_mcp_write_requires_read(self):
        with pytest.raises(RuntimeError, match="MCP_WRITE_ENABLED"):
            _settings(env="development", mcp_write_enabled=True, mcp_read_enabled=False)

    def test_verified_gateway_requires_every_credential(self):
        with pytest.raises(RuntimeError, match="Verified gateway"):
            _settings(
                env="development",
                llm_gateway_governance_verified=True,
                llm_gateway_base_url="http://gateway",
                llm_gateway_api_key="",
                llm_gateway_admin_key="",
                llm_gateway_v2_team_id="",
            )

    def test_content_receipts_require_keys_and_issuer(self):
        with pytest.raises(RuntimeError, match="Content receipt"):
            _settings(env="development", content_receipts_enabled=True)

    def test_complete_streaming_chain_is_accepted_and_default_off(self):
        configured = _settings(
            env="development",
            teaching_runs_enabled=True,
            teaching_dialogue_enabled=True,
            teaching_streaming_enabled=True,
            llm_gateway_governance_verified=True,
            llm_gateway_base_url="http://gateway",
            llm_gateway_api_key="service",
            llm_gateway_admin_key="admin",
            llm_gateway_v2_team_id="team",
        )
        assert configured.teaching_streaming_enabled
        assert configured.llm_gateway_tutor_max_tokens == 1024
        assert _settings(env="development").teaching_streaming_enabled is False

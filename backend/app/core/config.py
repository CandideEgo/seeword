import re
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The environments the app knows how to behave under. A value outside this set
# is a misconfiguration, never a third mode: it used to match neither the
# development defaults nor the production guards in ``model_post_init``, so the
# app booted with an empty ``jwt_secret`` — JWTs signed with an empty key — and
# silently skipped every guard. ``.env.example`` documents the same three values.
# ``prod`` is folded into ``production`` because payment_provider already treats
# it as production; case/whitespace variants are normalized so an accepted
# spelling cannot miss the downstream ``settings.env == "production"`` checks
# (HSTS/CSP, JSON logs, mock-payment router, rate limits).
_ENV_ALIASES = {"prod": "production"}
_ENV_VALUES = ("development", "testing", "production")

# Only HMAC algorithms are supported: ``create_token``/``decode_token`` sign with
# a shared secret, so an env value of e.g. ``"none"`` or an asymmetric algorithm
# name must not be accepted just because PyJWT would parse it.
_JWT_ALGORITHMS = ("HS256", "HS384", "HS512")

# HS256 keys shorter than the hash output (32 bytes) are cheap to brute-force.
# production/testing must provide at least this many characters.
_MIN_JWT_SECRET_LENGTH = 32
_DEV_JWT_SECRET = "dev_secret_change_in_production"


class Settings(BaseSettings):
    app_name: str = "SeeWord"
    debug: bool = False

    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = ""
    env: str = "development"
    jwt_algorithm: str = "HS256"
    # Access token TTL (minutes). Short so a stolen token has a small window;
    # the frontend auto-refreshes via the refresh token (authStore).
    jwt_expire_minutes: int = 30
    # Refresh token TTL (days). Wired in security.create_token (the historical
    # "4x access" formula was replaced by this explicit knob).
    jwt_refresh_expire_days: int = 7
    jwt_blacklist_enabled: bool = True
    bcrypt_rounds: int = 12

    # Alibaba Cloud Dypnsapi — SMS verification code for phone login / change
    # phone / reset password (SendSmsVerifyCode / CheckSmsVerifyCode: the code
    # is generated and verified server-side by Aliyun). The fixed-code dev fake
    # ("1234") is opt-in via sms_dev_fake_enabled and only allowed outside
    # production; without it, missing AK/SK fail closed.
    sms_login_enabled: bool = False
    # Explicit opt-in for the fixed-code dev fake ("1234"). Required for local
    # dev / CI phone flows; if ENV is forgotten in a deployment this stays
    # False, so the fake cannot silently turn a public box into "any phone can
    # log in with 1234". Refused outright in production.
    sms_dev_fake_enabled: bool = False
    aliyun_sms_access_key: str = ""
    aliyun_sms_secret_key: str = ""
    aliyun_sms_sign_name: str = "速通互联验证码"
    aliyun_sms_template_register: str = "100001"
    aliyun_sms_template_change_phone: str = "100002"
    aliyun_sms_template_reset_password: str = "100003"
    sms_code_expire_seconds: int = 300  # 5 minutes
    # Dypnsapi 短信认证服务 endpoint（SendSmsVerifyCode / CheckSmsVerifyCode）。
    aliyun_sms_endpoint: str = "dypnsapi.aliyuncs.com"

    # Legacy OpenAI-compatible gateway (kept as a fallback provider). AIService
    # prefers COMMANDCODE_* below when that key is set.
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o"

    # Command Code LLM provider (OpenAI-compatible ``/chat/completions``).
    # Defaults to the provider's free model so the video pipeline and the
    # homepage draft generator work without per-token spend; the model catalog
    # (free flags, context windows, ZDR support) lives in
    # ``app/services/llm_provider.py`` — one fact, one home.
    # Free models are promotional (provider may withdraw them at any time):
    # re-run ``python scripts/check_llm_provider.py --list`` to audit.
    commandcode_api_key: str = ""
    commandcode_base_url: str = "https://api.commandcode.ai/provider/v1"
    commandcode_model: str = "minimax/minimax-m3.1-flash:free"
    # Per-request zero-data-retention (``x-cmd-zdr: 1``). Opt-in: some free
    # models cannot run under ZDR and the gateway hard-fails rather than
    # degrading, so enable it only with a ZDR-capable model pinned above.
    commandcode_zdr: bool = False
    # Per-task model overrides (empty = commandcode_model). Tasks are defined in
    # ``app/services/llm_provider.py``: translation / word_notes /
    # classification / editorial. Lets cheap batch work and editorial drafts
    # use different models without touching call sites.
    llm_model_translation: str = ""
    llm_model_word_notes: str = ""
    llm_model_classification: str = ""
    llm_model_editorial: str = ""
    # Hard timeout (seconds) for a single LLM chat call (AIService).
    llm_call_timeout: int = 90

    # V2 is opt-in. A blank allowlist authorizes nobody, including in development.
    teaching_enabled: bool = False
    teaching_runs_enabled: bool = False
    teaching_dialogue_enabled: bool = False
    # P02.2: streamed tutor replies. Requires dialogue; off keeps the legacy
    # non-streaming JSON reply and never touches the block tables.
    teaching_streaming_enabled: bool = False
    teaching_allowed_user_ids: str = ""
    mcp_read_enabled: bool = False
    mcp_write_enabled: bool = False
    mcp_sdk_enabled: bool = False
    mcp_allowed_hosts: str = "localhost,127.0.0.1,testserver"
    mcp_allowed_origins: str = ""
    llm_gateway_base_url: str = ""
    llm_gateway_api_key: str = ""
    llm_gateway_admin_key: str = ""
    llm_gateway_governance_verified: bool = False
    llm_gateway_model: str = "teaching"
    # The streamed tutor uses its own alias/cap so the verified 128-token
    # cards/content-verification envelope is never silently widened.
    llm_gateway_tutor_model: str = "teaching-tutor"
    llm_gateway_tutor_max_tokens: int = Field(default=1024, ge=128, le=4096)
    llm_gateway_v2_team_id: str = ""
    content_receipts_enabled: bool = False
    content_verification_api_key: str = Field(default="", repr=False)
    content_receipt_public_keys: dict[str, str] = Field(default_factory=dict, repr=False)
    content_receipt_issuer: str = "seeword-content-gateway"
    content_receipt_max_age_seconds: int = Field(default=86400, ge=60, le=86400)
    v2_daily_budget_usd: float = Field(default=1.0, gt=0, le=1.0)
    v2_user_daily_budget_usd: float = Field(default=0.10, gt=0, le=0.10)
    v2_run_budget_usd: float = Field(default=0.02, gt=0, le=0.02)
    teaching_run_retention_hours: int = 24
    teaching_usage_retention_days: int = 7

    local_media_path: str = "./media"

    # 真题原卷 PDF（data/exam_pdfs/index.json + files/*.pdf）。默认值即生产值：
    # 容器 WORKDIR 是 /app，bind mount 把 ./backend/data 挂到 /app/data，所以
    # 相对路径在生产与本地都指到同一处，不需要新增任何 env / compose 项。
    exam_pdf_dir: str = "./data/exam_pdfs"

    # Local video upload limits + temp dir (used by upload_service).
    max_upload_file_size: int = 500 * 1024 * 1024  # 500 MB
    upload_temp_dir: str = "./media/uploads"

    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_access_key: str = ""
    oss_secret_key: str = ""
    # When False (default), OSS is treated as disabled and upload helpers degrade
    # gracefully — no SDK required to run the app.
    oss_upload_enabled: bool = False
    oss_prefix: str = ""
    oss_cdn_domain: str = ""

    # Remote-GPU transcription pipeline. The cloud enqueues a transcription task
    # onto the ``transcription_gpu`` queue (consumed by a GPU worker on a separate
    # machine); the GPU worker transcribes and POSTs the subtitles back to this
    # callback URL. The shared secret authenticates the inbound callback.
    transcription_callback_url: str = ""
    transcription_callback_secret: str = ""
    transcription_gpu_queue_name: str = "transcription_gpu"
    transcription_callback_timeout: int = 30  # seconds per HTTP attempt
    transcription_callback_max_retries: int = 5  # 5xx / connection retries
    # Watchdog: a video stuck in "transcribing" longer than this (seconds) is
    # assumed to have lost its GPU worker and is marked failed.
    video_transcribe_timeout: int = 7200  # 2 hours

    # Watchdog per-step timeouts (seconds). A video whose ``step_started_at`` is
    # older than its step's timeout is assumed stuck (worker crashed / hung LLM
    # call / dead ffmpeg) and marked failed by ``watchdog_stale_pipeline``.
    # Per-step (not whole-pipeline) so a stuck translate isn't masked by a wide
    # transcribe timeout. Unmapped steps fall back to ``_default``.
    pipeline_step_timeout_extracting: int = 600  # 10 min (yt-dlp metadata)
    pipeline_step_timeout_translating: int = 1800  # 30 min (LLM batch + retries)
    pipeline_step_timeout_annotating: int = 300  # 5 min (pure ECDICT local)
    pipeline_step_timeout_prewarm_notes: int = 1800  # 30 min (LLM batch)
    pipeline_step_timeout_classifying: int = 600  # 10 min (one LLM call, 60s hard timeout)
    pipeline_step_timeout_downloading: int = 3600  # 60 min (yt-dlp download)
    pipeline_step_timeout_transcoding: int = 1800  # 30 min (ffmpeg)
    pipeline_step_timeout_default: int = 3600  # fallback for unmapped steps

    # A05/BE-01: durable pipeline dispatch (``pipeline_dispatches`` outbox).
    # Settled rows (sent / abandoned) are pruned after this window; the beat
    # dispatcher alerts when the undelivered backlog is bigger than the
    # threshold or older than the age limit (throttled to one alert / 30 min).
    pipeline_dispatch_retention_hours: int = 72
    pipeline_dispatch_backlog_alert_threshold: int = 5
    pipeline_dispatch_backlog_alert_age_seconds: int = 1800

    # Translation quality gate (阶段 2 of PIPELINE-QUALITY-IMPROVEMENTS-2026-07).
    # Coverage below ``translation_quality_block_coverage`` -> ``quality_blocked``
    # + ``status=error``, and the pipeline stops WITHOUT a Celery retry (same
    # engine on the same input reproduces the low coverage); admin re-translates,
    # possibly with another engine, via admin retranslate. Between the block and
    # warn thresholds -> ``quality_warning`` but still ready. Set
    # ``translation_quality_block_enabled=False`` for warn-only (kill switch).
    translation_quality_block_enabled: bool = True
    translation_quality_block_coverage: float = 0.60  # < this -> blocked (error)
    translation_quality_warn_coverage: float = 0.80  # < this (>= block) -> warning

    # Download retry (阶段 3). Max automatic re-attempts for failed YouTube/
    # imported downloads before the beat task gives up (permanent failure).
    download_retry_max_attempts: int = 3

    # OSS raw-media transfer for locally-uploaded videos. The cloud uploads the
    # raw upload to OSS and hands the GPU worker a (signed) URL — the GPU worker
    # needs no OSS credentials of its own.
    oss_raw_prefix: str = "video/raw"
    oss_raw_bucket_public: bool = False  # False → use signed URLs (private bucket)
    oss_signed_url_expiry: int = 7200  # seconds; must exceed max queue wait + transcribe

    # Payment configuration
    default_payment_provider: str = "mock"  # mock | alipay | wechat
    alipay_app_id: str = ""
    alipay_public_key: str = ""
    alipay_private_key: str = ""
    wechat_mch_id: str = ""
    wechat_api_v3_key: str = ""
    wechat_serial_no: str = ""
    payment_verify_signature: bool = True
    # 审计 H12：默认必须 fail-closed。旁路「env=development 且本 flag 为 False」
    # 才生效（alipay/wechat _verify_*），而 env 默认也是 development —— 两个默认
    # 叠加曾构成「漏配 ENV + 开支付 = 可伪造回调」。dev 要跳过验签须显式
    # PAYMENT_VERIFY_SIGNATURE=False（有 warning 日志）。
    # ICP 合规：个体工商户无 ICP 经营许可证，不能站内收款。默认禁用站内支付，
    # create-order 端点返回合规提示；取得相应资质后置 True 恢复站内支付链路。
    payments_enabled: bool = False

    # 金数据（外部收款页）→ 自动开通 Pro。站内仍不开收款（ICP 合规），会员在
    # 托管于金数据的收款页成交后，由 Celery beat 定时同步 + 可选的数据推送
    # webhook 落账，并按买家手机号延长对应账号的 plan_expires_at。
    # Access Token 与表单 token 只允许放服务端 env，不要进前端或仓库。
    jinshuju_enabled: bool = False
    jinshuju_access_token: str = ""
    jinshuju_form_token: str = ""  # 表单 token，例如 ed8TXL
    # 数据推送 URL 上要求的共享密钥；为空时 webhook 一律拒绝（fail-closed）。
    jinshuju_webhook_secret: str = ""
    # 表单里「档位」商品字段与「手机号」字段的 api_code（表单字段改版时同步改）。
    jinshuju_tier_field: str = "field_2"
    jinshuju_phone_field: str = "field_5"
    # 每轮同步回看多少小时内的数据（补漏 webhook；公测量级下一次请求足够）。
    jinshuju_sync_lookback_hours: int = 72
    # 站内购买：快捷收款页地址 + 写在 x_field_1 里的签名 token。
    # x_field_1 本身没有签名保护，所以值做成「user_id + 过期时间 + HMAC」的
    # 紧凑 token：篡改/过期都会验签失败，不会把会员发错人。
    jinshuju_purchase_url: str = ""  # 例如 https://xxx.jsjform.com/p/ed8TXL
    # 站内购买 token 的 HMAC 密钥。**不回退 JWT_SECRET**：一把密钥同时保护
    # 「用户会话」与「购买凭证」两个不同用途，密钥分离就没了。缺失时签发与
    # 验签一律失败（见 ``jinshuju_service._purchase_secret``）。
    jinshuju_purchase_token_secret: str = ""
    jinshuju_purchase_token_ttl_minutes: int = 1440

    # Free-tier video unlock quota (产品设计规划 §2.2): Free users may unlock
    # this many videos per calendar month; each unlock is permanent. Quotas
    # reset on the 1st, unused quotas do not roll over.
    free_monthly_unlock_quota: int = 3
    # Signup trial: new registrations get Pro for this many days (plan_source='trial').
    trial_days: int = 3

    # Proxy for external services (yt-dlp, AI)
    http_proxy: str = ""  # e.g. http://172.25.176.1:7897
    youtube_cookies_path: str = ""  # e.g. ./youtube_cookies.txt
    # bgutil POT provider (proof-of-origin token) HTTP server — needed to clear
    # YouTube's "Sign in to confirm you're not a bot" gate. Must be passed to the
    # plugin explicitly: left to its default the plugin's own request goes through
    # http_proxy, which can't reach the host loopback and times out.
    youtube_pot_base_url: str = "http://127.0.0.1:4416"

    # Max video resolution to download (height). Production runs on a 40G disk /
    # 2-core VPS, so the default is 720p (~9.5 MB/min). Raise to 1080 after
    # expanding disk capacity — the change is config-only, no code edit needed.
    video_max_height: int = 720

    # Observability
    sentry_dsn: str = ""
    log_level: str = "INFO"
    # External alert channel (E4): a webhook URL (DingTalk / Slack / generic
    # JSON POST) that alert_service.send_alert posts to. Empty = alerts fall
    # back to in-app notify_admins only (no out-of-band channel).
    alert_webhook_url: str = ""
    alert_webhook_secret: str = ""  # DingTalk sign secret (optional)

    # A09/OPS-05: web-process health monitor. It watches the worker/beat
    # heartbeats, queue depth, disk and the pipeline failure rate, and sends
    # the same off-site webhook alert. Thresholds are settings so ops can tune
    # them without a rebuild; probes are per-kind throttled in Redis.
    #
    # Opt-in (compose passes HEALTH_MONITOR_ENABLED=true for production): in a
    # dev checkout beat/worker may be intentionally off, and the monitor would
    # then alert every throttle window and write in-app admin notifications.
    health_monitor_enabled: bool = False
    health_monitor_interval_seconds: int = 60
    health_worker_stale_seconds: int = 300
    health_beat_stale_seconds: int = 300
    health_queue_backlog_threshold: int = 200
    health_disk_percent_threshold: int = 85
    health_pipeline_failure_threshold: int = 5
    health_pipeline_failure_window_minutes: int = 60
    health_alert_throttle_seconds: int = 1800

    # Speech-transcription settings (WHISPER_* / TRANSCRIPTION_TEMP_DIR) have
    # moved to the standalone ``gpu-worker/`` component: the cloud no longer
    # runs Whisper. Only the queue name / callback knobs stay here — see the
    # "Remote-GPU transcription pipeline" block above.

    # Translation engine (pluggable). Agnes is retired for translation (prone
    # to missed/low-quality output); qwen + hy_mt2 (both iFLYTEK) are the
    # default pair. Agnes is still used by AIService._chat for non-translation
    # LLM calls (pronunciation/rubric/gloss/grammar/practice questions).
    translation_engine: str = "qwen"  # qwen | hy_mt2 | agnes | glm | custom
    translation_fallback_engine: str = "hy_mt2"  # paired with primary for concurrent mode
    translation_concurrent: bool = True  # run primary + fallback concurrently, first valid wins
    translation_batch_size: int = 5  # smaller batches avoid 404s (agnes) and sentence-merging (hy_mt2)
    translation_hymt2_api_key: str = ""
    translation_qwen_api_key: str = ""
    translation_glm_api_key: str = ""
    translation_glm_base_url: str = "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2"
    translation_glm_model: str = "xopglm51"
    translation_custom_base_url: str = ""
    translation_custom_model: str = ""
    translation_custom_api_key: str = ""

    # Per-video AI word-notes prewarm (finalize_video.prewarm_notes step).
    # Comma-separated list of engines to fan batches across concurrently.
    # "agnes" uses OPENAI_*; others resolve via the translation engine
    # registry (same creds as TRANSLATION_*_API_KEY). Set to "agnes" alone
    # to keep the old single-engine sequential behavior.
    prewarm_engines: str = "agnes,qwen"
    prewarm_concurrency: int = 4  # max in-flight LLM calls per engine

    # Video scoring (P1, ADR-0011 + 阶段 2). 7-factor weighted learning_score
    # (0-100) computed by scoring_service + refreshed by scoring beat tasks.
    # Weights are applied to 0-1 factor values and sum to 1.0;
    # ``score_bonus_points`` is additive on top of the 0-100 weighted base
    # (not a weight). All tunable via env so scoring can be retuned without
    # code changes. See LAUNCH-SPRINT-2026-07 阶段 4. No-data phase:
    # CTR/Retention/WatchTime/Viral/Freshness stay 0 (no redistribution);
    # TopicMatch/Quality/Bonus give new videos a non-zero baseline.
    # 阶段 2 rebalance: external-signal factors (viral/freshness) take 0.15
    # from the original five (weights reduced proportionally).
    score_weight_ctr: float = 0.25
    score_weight_retention: float = 0.22
    score_weight_watch_time: float = 0.18
    score_weight_topic_match: float = 0.12
    score_weight_quality: float = 0.08
    score_weight_viral: float = 0.08
    score_weight_freshness: float = 0.07
    score_bonus_points: float = 10.0  # additive bonus (max +10 points)
    # Saturation benchmarks: the count at which a factor reaches 1.0.
    score_ctr_click_benchmark: int = 50  # 50 clicks → CTR factor 1.0
    score_watch_time_benchmark: int = 36000  # 10h total watch → WatchTime factor 1.0
    # Freshness benchmark: views-per-day on YouTube that saturates the factor
    # (10k/day ≈ "1M views in 100 days"-class momentum; 1M/10d = 100k/day
    # saturates instantly, a 5-year-old 10M video sits around 5.5k/day ≈ 0.55).
    score_freshness_vpd_benchmark: int = 10000

    # Home feed recommendation (P2, ADR-0011). 40/30/20/10 mix of
    # high-score / potential / cold-start / long-form videos, plus diversity
    # (same topic_tags ≤N consecutive) and soft personalization (history click
    # topic_tags + target_exam/level CEFR match — NOT a hard filter, since
    # videos have no exam_level field and a hard filter would empty a 13-video
    # pool). Ratios must sum to ~1.0; shortfall buckets backfill from top.
    # See LAUNCH-SPRINT-2026-07 阶段 5.
    recommend_ratio_top: float = 0.40
    recommend_ratio_potential: float = 0.30
    recommend_ratio_cold: float = 0.20
    recommend_ratio_long: float = 0.10
    recommend_cold_start_days: int = 7  # created_at within N days → cold bucket
    recommend_long_duration_min: int = 1200  # duration (s) → long-form bucket
    recommend_min_score_for_long: float = 30.0  # long-form must clear this score
    recommend_consecutive_tag_max: int = 2  # max consecutive same first-topic
    recommend_min_clicks_for_personalization: int = 3  # below this → global sort
    recommend_home_ttl_seconds: int = 60  # Redis cache TTL for home feed
    # Sprint 3: vocab recurrence boost — max score added to videos containing
    # words the user is actively learning (mastery_level in learning/reviewing).
    recommend_vocab_boost_max: float = 5.0
    recommend_vocab_word_limit: int = 200  # max learning words to consider

    # 首页排行榜快照 TTL（Redis，秒）。snapshot-rankings beat 任务每日 01:23 UTC
    # 重算三个榜单（latest / weekly_views / weekly_favorites）并覆写快照；
    # GET /videos/rankings 读穿这些快照，Redis 故障时 fail-open 直接查库。
    rankings_snapshot_ttl_seconds: int = 172800  # 48h

    # 半自动下线阈值（需求 §5.3）：上线满 N 天 + 播放/收藏均低于阈值 →
    # 进入「建议下线」候选，由管理员一键确认。仅建议，不自动执行。
    takedown_min_age_days: int = 30
    takedown_min_views: int = 100
    takedown_min_favorites: int = 5

    # Frontend URL for CORS
    frontend_url: str = "http://localhost:3000"
    # Extra domains allowed by the production Content-Security-Policy connect-src
    # directive (space-separated), e.g. "https://api.openai.com".
    csp_connect_domains: str = ""

    # Docker/Compose injects extra env vars (e.g. PGHOST, PGDATABASE);
    # ignore them rather than raising validation errors.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        """Apply development defaults, then guard every non-development env.

        ``env`` selects between local defaults and hardening, so an unknown
        value must not land in a branch with neither: fail closed instead.
        """
        env = self.env.strip().lower()
        env = _ENV_ALIASES.get(env, env)
        if env not in _ENV_VALUES:
            raise RuntimeError(
                f"ENV={self.env!r} is not a recognized environment ({', '.join(_ENV_VALUES)}). "
                "Refusing to start: an unrecognized value gets neither the development "
                "defaults nor the production guards."
            )
        # Store the normalized value so every downstream ``settings.env``
        # comparison (logging, HSTS/CSP, CORS, limiter) sees the same string.
        object.__setattr__(self, "env", env)

        if self.content_receipts_enabled:
            from app.services.teaching.content_receipts import public_key

            if not self.content_receipt_public_keys or not self.content_receipt_issuer.strip():
                raise RuntimeError("Content receipt verification requires public keys and an issuer")
            if len(self.content_receipt_public_keys) > 5:
                raise RuntimeError("At most five content receipt public keys may be active")
            for kid, pem in self.content_receipt_public_keys.items():
                try:
                    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kid):
                        raise ValueError("invalid key ID")
                    public_key(pem)
                except (ValueError, TypeError) as exc:
                    raise RuntimeError("Invalid content receipt Ed25519 public key configuration") from exc

        if self.mcp_write_enabled and not self.mcp_read_enabled:
            raise RuntimeError("MCP_WRITE_ENABLED requires MCP_READ_ENABLED")
        if self.teaching_runs_enabled and not self.llm_gateway_governance_verified:
            raise RuntimeError("TEACHING_RUNS_ENABLED requires verified gateway governance")
        if self.teaching_dialogue_enabled and not self.teaching_runs_enabled:
            raise RuntimeError("TEACHING_DIALOGUE_ENABLED requires TEACHING_RUNS_ENABLED")
        if self.teaching_streaming_enabled and not self.teaching_dialogue_enabled:
            raise RuntimeError("TEACHING_STREAMING_ENABLED requires TEACHING_DIALOGUE_ENABLED")
        if self.llm_gateway_governance_verified and not all(
            (
                self.llm_gateway_base_url,
                self.llm_gateway_api_key,
                self.llm_gateway_admin_key,
                self.llm_gateway_v2_team_id,
            )
        ):
            raise RuntimeError("Verified gateway requires base URL, service/admin keys and V2 team ID")

        # The signing algorithm is an attack surface, not a preference: a typo
        # or an injected value must fail at boot, not at the first token check.
        algorithm = self.jwt_algorithm.strip().upper()
        if algorithm not in _JWT_ALGORITHMS:
            raise RuntimeError(
                f"JWT_ALGORITHM={self.jwt_algorithm!r} is not supported "
                f"({', '.join(_JWT_ALGORITHMS)} are the only accepted HMAC algorithms)"
            )
        object.__setattr__(self, "jwt_algorithm", algorithm)

        if env == "development":
            if not self.database_url:
                object.__setattr__(
                    self, "database_url", "postgresql+asyncpg://seeword:seeword_dev@localhost:5432/seeword"
                )
            if not self.jwt_secret:
                object.__setattr__(self, "jwt_secret", _DEV_JWT_SECRET)
            return

        # Every other env has no localhost fallback, so an empty secret must
        # fail here rather than reach JWT signing. Checked outside the
        # "production" branch so `ENV=testing` cannot become a way around it.
        if not self.jwt_secret:
            raise RuntimeError(f"JWT_SECRET must be set when ENV={env!r} (development is the only env with a fallback)")
        # Non-empty is not enough: a 1-character key makes HS256 forgeable by
        # brute force (anyone can mint an access token for any user, admins
        # included). Testing is covered too so CI cannot grow a weak-secret habit.
        if self.jwt_secret == _DEV_JWT_SECRET or len(self.jwt_secret) < _MIN_JWT_SECRET_LENGTH:
            raise RuntimeError(
                f"JWT_SECRET must be at least {_MIN_JWT_SECRET_LENGTH} characters and must not be the "
                f"development default when ENV={env!r}. Generate one with: openssl rand -hex 32"
            )
        if not self.database_url:
            raise RuntimeError(
                f"DATABASE_URL must be set when ENV={env!r} (development is the only env with a fallback)"
            )
        if env == "production":
            if self.sms_dev_fake_enabled:
                raise RuntimeError(
                    "SMS_DEV_FAKE_ENABLED must not be enabled in production "
                    "(the fixed code '1234' would let anyone log into any phone account)"
                )
            # 站内微信/支付宝回调验签目前是 stub（HMAC 而非平台 RSA 证书），
            # 一旦被误开，合法回调会被拒、伪造回调可能开通会员。生产入口是
            # 金数据收款页；要开站内支付必须先实现官方验签并删掉这条 guard。
            if self.payments_enabled:
                raise RuntimeError(
                    "PAYMENTS_ENABLED must stay false in production: the WeChat/Alipay callback "
                    "verification is a stub until the official RSA/signature SDK is wired. "
                    "Use the Jinshuju payment flow instead."
                )
            # The guard is "an LLM key must exist", not "the OpenAI key must
            # exist": production may run entirely on the Command Code provider.
            # An empty pair is still fatal — features would fail at call time.
            if not (
                self.openai_api_key.strip()
                or self.commandcode_api_key.strip()
                or (self.llm_gateway_base_url.strip() and self.llm_gateway_api_key.strip())
            ):
                raise RuntimeError(
                    "OPENAI_API_KEY or COMMANDCODE_API_KEY or an internal LLM gateway must be set in production"
                )
            # ``redis_url`` carries a working localhost default (Celery broker,
            # rate-limit storage, cache client), so a forgotten REDIS_URL reaches
            # here as a non-empty string; require it to have been provided.
            if not self.redis_url or "redis_url" not in self.model_fields_set:
                raise RuntimeError("REDIS_URL must be set in production")
            if not self.transcription_callback_secret:
                raise RuntimeError("TRANSCRIPTION_CALLBACK_SECRET must be set in production")
            # 金数据站内购买 token 的 HMAC 密钥：必须显式配置，且不得复用
            # JWT_SECRET —— 同一把密钥保护「用户会话」与「购买凭证」两个不同
            # 用途就是密钥分离被破坏。只在开启金数据时要求（关着就无所谓）。
            if self.jinshuju_enabled:
                if not self.jinshuju_purchase_token_secret:
                    raise RuntimeError(
                        "JINSHUJU_PURCHASE_TOKEN_SECRET must be set in production "
                        "when JINSHUJU_ENABLED=true (it does NOT fall back to JWT_SECRET)"
                    )
                if self.jinshuju_purchase_token_secret == self.jwt_secret:
                    raise RuntimeError("JINSHUJU_PURCHASE_TOKEN_SECRET must differ from JWT_SECRET in production")
                if not (self.jinshuju_access_token.strip() and self.jinshuju_form_token.strip()):
                    raise RuntimeError(
                        "JINSHUJU_ACCESS_TOKEN and JINSHUJU_FORM_TOKEN must be set in production "
                        "when JINSHUJU_ENABLED=true"
                    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Pluggable translation engine for subtitle translation.

Usage::

    from app.services.translation import get_translation_service

    service = get_translation_service()
    results = await service.translate_batch(["Hello", "Goodbye"])

Engine selection is controlled by ``TRANSLATION_ENGINE`` in .env.
If ``TRANSLATION_FALLBACK_ENGINE`` is set, failures fall back automatically.
"""

import asyncio
import copy
import json
import threading

import structlog
from openai import AsyncOpenAI

from app.core.capabilities import require_llm
from app.core.config import get_settings
from app.core.errors import BadRequestError, ServiceUnavailableError
from app.services.llm_provider import COMMANDCODE_DEFAULT_BASE_URL, TASK_TRANSLATION, resolve_model

from .engines import BUILTIN_ENGINES, DEFAULT_TRANSLATION_PROMPT, EngineConfig
from .json_sanitizer import sanitize_json

logger = structlog.get_logger()


class TranslationService:
    """Pluggable translation service using OpenAI-compatible engines.

    Always obtain via ``get_translation_service()`` — never instantiate directly.
    """

    def __init__(self, engine_override: str | None = None) -> None:
        require_llm()
        settings = get_settings()
        # engine_override: force a specific primary engine. Used by admin
        # re-translate to retry with a different engine after a quality block
        # (same engine + same input would reproduce the low coverage). When set,
        # no fallback is configured and concurrent mode is disabled - the admin
        # asked for this one engine specifically.
        self._engine_name = engine_override or settings.translation_engine or "agnes"
        self._fallback_name = None if engine_override else (settings.translation_fallback_engine or None)
        self._batch_size = settings.translation_batch_size or 20
        self._concurrent = settings.translation_concurrent and not engine_override

        self._engine = self._resolve_engine(self._engine_name, settings)
        self._fallback = self._resolve_engine(self._fallback_name, settings) if self._fallback_name else None

        # Create AsyncOpenAI client for each engine
        self._client = self._make_client(self._engine)
        self._fallback_client = self._make_client(self._fallback) if self._fallback else None

        logger.info(
            "TranslationService initialized",
            engine=self._engine.label,
            fallback=self._fallback.label if self._fallback else None,
            concurrent=self._concurrent,
            batch_size=self._batch_size,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def translate_batch(self, texts: list[str]) -> list[str | None]:
        """Translate a batch of English texts to Chinese.

        In concurrent mode (default when a fallback engine is configured),
        primary + fallback run simultaneously and the first valid result wins
        — the sibling call is cancelled. This mirrors the prewarm dual-engine
        pattern and is far more robust against one engine intermittently
        failing (the symptom behind "some subtitles translated, some not").

        In sequential mode, the primary is tried first and the fallback only
        on primary failure.
        """
        if not texts:
            return []

        engines = [(self._client, self._engine)]
        if self._fallback and self._fallback_client:
            engines.append((self._fallback_client, self._fallback))

        if self._concurrent and len(engines) > 1:
            return await self._translate_concurrent(engines, texts)

        # Sequential primary → fallback
        result = await self._call_engine(self._client, self._engine, texts)
        if result is not None:
            return result

        if self._fallback and self._fallback_client:
            logger.warning(
                "Primary translation engine failed, trying fallback",
                primary=self._engine.name,
                fallback=self._fallback.name,
            )
            result = await self._call_engine(self._fallback_client, self._fallback, texts)
            if result is not None:
                return result

        # Both failed
        logger.error("All translation engines failed", count=len(texts))
        return [None] * len(texts)

    async def _translate_concurrent(
        self,
        engines: list[tuple[AsyncOpenAI, EngineConfig]],
        texts: list[str],
    ) -> list[str | None]:
        """Fan out to every engine concurrently; first valid result wins.

        Losing tasks are cancelled so we don't pay for a second LLM call once
        we have a winner. If every engine returns ``None`` (failure), the
        caller gets ``[None] * len(texts)``.
        """
        tasks = [
            asyncio.create_task(self._call_engine(client, engine, texts), name=f"translate:{engine.name}")
            for client, engine in engines
        ]
        try:
            for awaitable in asyncio.as_completed(tasks):
                result = await awaitable
                if result is not None:
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    return result
        except Exception as exc:  # pragma: no cover — _call_engine swallows, but guard
            logger.error("Concurrent translation fan-out error", error=str(exc))
            for t in tasks:
                if not t.done():
                    t.cancel()
        logger.error(
            "All concurrent translation engines failed",
            count=len(texts),
            engines=[e.name for _, e in engines],
        )
        return [None] * len(texts)

    @property
    def engine_name(self) -> str:
        """Active engine name (for logging / diagnostics)."""
        return self._engine_name

    @property
    def batch_size(self) -> int:
        """Configured global batch size."""
        return self._batch_size

    @property
    def effective_batch_size(self) -> int:
        """Return per-engine batch size override or the global default.

        Uses the primary engine's ``batch_size`` if set (> 0); otherwise
        the global ``translation_batch_size``.  This is the batch size
        callers should use when splitting texts before calling
        ``translate_batch()``.
        """
        if self._engine.batch_size > 0:
            return self._engine.batch_size
        return self._batch_size

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_translations(items: list) -> list[str | None]:
        """Coerce a parsed LLM response into ``list[str | None]``.

        LLMs occasionally emit ``null`` / non-string / whitespace-only entries
        inside an otherwise well-formed JSON array. Treat those as missing
        (``None``) rather than passing junk through to the subtitle row, so a
        single bad slot doesn't silently misalign the write-back.
        """
        out: list[str | None] = []
        for p in items:
            if isinstance(p, str) and p.strip():
                out.append(p.strip())
            else:
                out.append(None)
        return out

    async def _call_engine(
        self,
        client: AsyncOpenAI,
        engine: EngineConfig,
        texts: list[str],
        *,
        _max_retries: int = 3,
        _base_delay: float = 2.0,
    ) -> list[str | None] | None:
        """Call one engine with exponential-backoff retry.

        Retries on transient failures (network errors, 5xx, timeouts,
        JSON parse errors). Does NOT retry on permanent errors (4xx,
        authentication failures, malformed responses that parse but are
        structurally wrong).

        Args:
            _max_retries: Maximum retry attempts (default 3).
            _base_delay: Initial delay in seconds (doubles each retry).
        """
        require_llm()
        payload = json.dumps(texts, ensure_ascii=False)
        system = engine.system_prompt or DEFAULT_TRANSLATION_PROMPT
        user = f"Translate:\n{payload}\nReturn JSON array only."

        last_exception: Exception | None = None
        for attempt in range(_max_retries + 1):
            if attempt > 0:
                delay = _base_delay * (2 ** (attempt - 1))
                logger.info(
                    "Translation retry %d/%d after %.1fs",
                    attempt,
                    _max_retries,
                    delay,
                    engine=engine.name,
                    batch_size=len(texts),
                )
                await asyncio.sleep(delay)

            try:
                resp = await client.chat.completions.create(
                    model=engine.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=engine.temperature,
                )
                raw = resp.choices[0].message.content or ""
                cleaned = sanitize_json(raw)
                parsed = json.loads(cleaned)

                if isinstance(parsed, list):
                    if len(parsed) == len(texts):
                        return self._normalize_translations(parsed)

                    if len(parsed) > len(texts):
                        # More results than expected — truncate
                        logger.warning(
                            "Translation result longer than input",
                            engine=engine.name,
                            expected=len(texts),
                            got=len(parsed),
                        )
                        return self._normalize_translations(parsed[: len(texts)])

                    # Shorter result — pad missing slots with None instead of
                    # discarding all valid translations.  The per-item retry in
                    # _translate_subtitles will attempt to fill the gaps.
                    logger.warning(
                        "Translation result shorter than input, padding with None",
                        engine=engine.name,
                        expected=len(texts),
                        got=len(parsed),
                    )
                    normalized = self._normalize_translations(parsed)
                    padded = normalized + [None] * (len(texts) - len(parsed))
                    return padded

                # Not a list at all — don't retry, this is a structural issue
                logger.warning(
                    "Translation result not a list",
                    engine=engine.name,
                    got_type=type(parsed).__name__,
                )
                return None

            except json.JSONDecodeError as exc:
                last_exception = exc
                logger.warning(
                    "Translation JSON parse error (attempt %d/%d)",
                    attempt + 1,
                    _max_retries + 1,
                    engine=engine.name,
                    error=str(exc),
                    raw_preview=raw[:200] if "raw" in dir() else "",
                )
                # JSON parse errors are retryable (often transient model glitches)
                continue
            except Exception as exc:
                last_exception = exc
                # Classify: 4xx / auth errors are permanent; others are retryable
                is_permanent = False
                if hasattr(exc, "status_code") and 400 <= exc.status_code < 500:
                    is_permanent = True
                elif "authentication" in str(exc).lower() or "api key" in str(exc).lower():
                    is_permanent = True

                if is_permanent:
                    logger.warning(
                        "Translation engine permanent error (no retry)",
                        engine=engine.name,
                        error=str(exc),
                    )
                    return None

                logger.warning(
                    "Translation engine call failed (attempt %d/%d)",
                    attempt + 1,
                    _max_retries + 1,
                    engine=engine.name,
                    error=str(exc),
                )
                continue

        # Exhausted all retries
        logger.error(
            "Translation engine exhausted all retries",
            engine=engine.name,
            attempts=_max_retries + 1,
            last_error=str(last_exception) if last_exception else None,
        )
        return None

    @staticmethod
    def _resolve_engine(name: str, settings) -> EngineConfig:
        """Look up an ``EngineConfig`` by name and fill in credentials from settings.

        Returns a **copy** so the original ``BUILTIN_ENGINES`` entry stays pristine.
        """
        if name not in BUILTIN_ENGINES:
            raise BadRequestError(f"Unknown translation engine: {name!r}. Available: {list(BUILTIN_ENGINES.keys())}")

        cfg = copy.deepcopy(BUILTIN_ENGINES[name])

        # Fill credentials from settings based on engine name
        if name == "hy_mt2":
            cfg.api_key = settings.translation_hymt2_api_key or cfg.api_key
        elif name == "qwen":
            cfg.api_key = settings.translation_qwen_api_key or cfg.api_key
        elif name == "agnes":
            # Backward compatibility: fall back to existing OPENAI_* vars
            cfg.base_url = cfg.base_url or settings.openai_base_url
            cfg.model = cfg.model or settings.openai_model
            cfg.api_key = cfg.api_key or settings.openai_api_key
        elif name == "glm":
            cfg.api_key = settings.translation_glm_api_key or cfg.api_key
            cfg.base_url = settings.translation_glm_base_url or cfg.base_url
            cfg.model = settings.translation_glm_model or cfg.model
        elif name == "custom":
            cfg.base_url = settings.translation_custom_base_url or cfg.base_url
            cfg.model = settings.translation_custom_model or cfg.model
            cfg.api_key = settings.translation_custom_api_key or cfg.api_key
        elif name == "commandcode":
            # Same provider as AIService (COMMANDCODE_*). The model resolves
            # through llm_provider so LLM_MODEL_TRANSLATION can pin a different
            # model than the rest of the app without forking the engine.
            cfg.base_url = settings.commandcode_base_url or COMMANDCODE_DEFAULT_BASE_URL
            cfg.model = resolve_model(settings, TASK_TRANSLATION)
            cfg.api_key = settings.commandcode_api_key
            if settings.commandcode_zdr:
                cfg.headers = {"x-cmd-zdr": "1"}

        # Validate required fields
        if not cfg.api_key:
            raise ServiceUnavailableError(
                f"Translation engine {name!r} has no API key configured. Set the engine's API key in .env "
                f"(TRANSLATION_*_API_KEY, or COMMANDCODE_API_KEY for the commandcode engine)."
            )
        if not cfg.base_url:
            raise ServiceUnavailableError(
                f"Translation engine {name!r} has no base_url configured. "
                f"Set the appropriate TRANSLATION_*_BASE_URL in .env."
            )
        if not cfg.model:
            raise ServiceUnavailableError(
                f"Translation engine {name!r} has no model configured. Set the appropriate TRANSLATION_*_MODEL in .env."
            )

        return cfg

    @staticmethod
    def _make_client(engine: EngineConfig) -> AsyncOpenAI:
        """Create an ``AsyncOpenAI`` client for the given engine config."""
        kwargs: dict = {
            "api_key": engine.api_key,
            "timeout": 300.0,  # 5 min — large batches need more time
        }
        if engine.base_url:
            kwargs["base_url"] = engine.base_url
        if engine.headers:
            kwargs["default_headers"] = dict(engine.headers)
        return AsyncOpenAI(**kwargs)

    @staticmethod
    def resolve_engine_client(name: str) -> tuple[AsyncOpenAI, str]:
        """Public API: resolve an engine name to ``(client, model)``.

        Used by AIService._get_engine_client to borrow translation-engine
        clients for non-translation LLM calls (e.g. prewarm fan-out) without
        reaching into private methods.
        """
        require_llm()
        cfg = TranslationService._resolve_engine(name, get_settings())
        client = TranslationService._make_client(cfg)
        return client, cfg.model


# ------------------------------------------------------------------
# Thread-safe singleton (same pattern as get_ai_service)
# ------------------------------------------------------------------

_translation_service: TranslationService | None = None
_singleton_lock = threading.Lock()


def get_translation_service() -> TranslationService:
    """Return the shared ``TranslationService`` singleton.

    Use this everywhere instead of creating ``TranslationService()`` instances,
    so a single set of ``AsyncOpenAI`` clients is reused across the process.
    Thread-safe for Celery workers that may call from multiple threads.
    """
    global _translation_service
    if _translation_service is None:
        with _singleton_lock:
            # Double-checked locking
            if _translation_service is None:
                _translation_service = TranslationService()
    return _translation_service

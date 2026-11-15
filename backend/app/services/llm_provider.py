"""LLM provider registry — the single place that answers "which model serves which task".

This adapts the provider/model design of ``earendil-works/pi`` (a single
``models.json`` with ``providers.<id>.{baseUrl, api, apiKey, models[]}`` and
explicit model metadata) to this repo's env-driven settings:

- one *provider* block resolves to ``baseUrl + api + apiKey + default model``
  (``COMMANDCODE_*`` today; legacy ``OPENAI_*`` is the fallback provider);
- the model catalog is explicit data (context window, free flag, ZDR support,
  daily limit), not runtime guesswork — ``free`` comes from the provider's
  published pricing page, while ``list_remote_models()`` audits the catalog
  against the live ``GET /models`` payload;
- a *task* (translation / word notes / classification / editorial) maps to a
  model, so the video pipeline and the homepage draft generator can be pointed
  at different models without touching call sites.

Nothing here imports an LLM SDK: no network client is built and no inference
happens. Client construction stays in ``app.services.ai_service`` and
``app.services.translation`` (INV-005). ``list_remote_models()`` talks to the
provider's ``/models`` endpoint only (a catalog read, not a completion call).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Task routing
# ---------------------------------------------------------------------------

TASK_DEFAULT = "default"
TASK_TRANSLATION = "translation"
TASK_WORD_NOTES = "word_notes"
TASK_CLASSIFICATION = "classification"
TASK_EDITORIAL = "editorial"

#: task -> ``Settings`` attribute carrying its model override. An empty value
#: means "use the provider's default model", so the env surface stays optional.
TASK_SETTINGS_FIELDS: dict[str, str] = {
    TASK_TRANSLATION: "llm_model_translation",
    TASK_WORD_NOTES: "llm_model_word_notes",
    TASK_CLASSIFICATION: "llm_model_classification",
    TASK_EDITORIAL: "llm_model_editorial",
}


# ---------------------------------------------------------------------------
# Provider / model specs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelSpec:
    """One model entry (pi's ``models[]`` item, trimmed to what this repo uses)."""

    id: str
    name: str = ""
    context_window: int = 0  # tokens; 0 = not recorded
    free: bool = False
    reasoning: bool = False
    zdr: bool = False  # whether the free/marked model runs under ZDR
    daily_limit: int | None = None
    source: str = ""  # where free / limit facts come from


@dataclass(frozen=True)
class ProviderSpec:
    """A resolved provider block (pi's ``providers.<id>``)."""

    name: str
    api: str  # pi's ``api`` values; only "openai-completions" is wired today
    base_url: str
    api_key: str
    model: str
    timeout: float
    zdr: bool = False

    @property
    def models_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/models"


#: Command Code's OpenAI-compatible gateway. ``COMMANDCODE_BASE_URL`` overrides it.
COMMANDCODE_DEFAULT_BASE_URL = "https://api.commandcode.ai/provider/v1"

#: Free models on Command Code, curated from the provider's pricing page
#: (https://commandcode.ai/docs/resources/pricing-limits, checked 2026-10-20)
#: and cross-checked against the live ``GET /models`` list. Order = preference
#: for free-tier work: ZDR-capable + no daily limit first, then capacity-only
#: previews, then the daily-capped stealth model.
#: These are *promotional*: the provider may withdraw them at any time, so they
#: are a fast/zero-cost default, not a production guarantee.
COMMANDCODE_FREE_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        id="minimax/minimax-m3.1-flash:free",
        name="MiniMax M3.1 Flash (free)",
        context_window=1_000_000,
        free=True,
        reasoning=True,
        zdr=True,
        source="https://commandcode.ai/docs/resources/pricing-limits (free for a limited time, no daily cap, ZDR)",
    ),
    ModelSpec(
        id="reflection/beam:free",
        name="Beam 1.0 (free)",
        context_window=1_000_000,
        free=True,
        reasoning=True,
        source="https://commandcode.ai/docs/resources/pricing-limits (free while capacity lasts, no daily cap, no ZDR)",
    ),
    ModelSpec(
        id="poolside/laguna-s-2.1-free",
        name="Laguna S 2.1 (free)",
        context_window=262_144,
        free=True,
        source="https://commandcode.ai/docs/resources/pricing-limits (free while capacity lasts, no daily cap)",
    ),
    ModelSpec(
        id="stealth/glyph-cluster:free",
        name="Glyph Cluster (free stealth)",
        context_window=262_144,
        free=True,
        reasoning=True,
        daily_limit=100,
        source="https://commandcode.ai/docs/resources/pricing-limits (stealth preview, 100 requests/day)",
    ),
)

#: First free model, i.e. the default when ``COMMANDCODE_MODEL`` is empty.
DEFAULT_COMMANDCODE_MODEL = COMMANDCODE_FREE_MODELS[0].id

_FREE_SUFFIX_MARKERS = (":free", "-free")


def is_free_model_id(model_id: str) -> bool:
    """Whether a model id is marked free by the gateway's naming convention.

    Command Code (like OpenRouter) marks promotional models in the id itself:
    ``minimax/minimax-m3.1-flash:free`` or ``poolside/laguna-s-2.1-free``.
    The ``GET /models`` payload carries no price field, so this suffix is the
    only per-model free signal available at runtime.
    """
    last_segment = model_id.strip().lower().rsplit("/", 1)[-1]
    return last_segment.endswith(_FREE_SUFFIX_MARKERS)


def catalog_lookup(model_id: str) -> ModelSpec | None:
    """Look a model id up in the curated free catalog (``None`` when unknown)."""
    for spec in COMMANDCODE_FREE_MODELS:
        if spec.id == model_id:
            return spec
    return None


def free_model_ids() -> list[str]:
    """Curated free model ids in preference order."""
    return [spec.id for spec in COMMANDCODE_FREE_MODELS]


# ---------------------------------------------------------------------------
# Provider resolution
# ---------------------------------------------------------------------------


def resolve_provider(settings: Settings | None = None) -> ProviderSpec | None:
    """Resolve the active provider, or ``None`` when no API key is configured.

    ``COMMANDCODE_API_KEY`` wins over the legacy ``OPENAI_*`` pair so switching
    providers is a pure env change (and an empty key keeps every caller working
    in keyless tests/CI — they fail loudly at call time instead).
    """
    s = settings or get_settings()
    if not s.llm_enabled:
        return None
    timeout = float(s.llm_call_timeout)
    if s.commandcode_api_key.strip():
        return ProviderSpec(
            name="commandcode",
            api="openai-completions",
            base_url=(s.commandcode_base_url or COMMANDCODE_DEFAULT_BASE_URL).strip(),
            api_key=s.commandcode_api_key.strip(),
            model=(s.commandcode_model or DEFAULT_COMMANDCODE_MODEL).strip(),
            timeout=timeout,
            zdr=bool(s.commandcode_zdr),
        )
    if s.openai_api_key.strip():
        return ProviderSpec(
            name="openai-compatible",
            api="openai-completions",
            base_url=s.openai_base_url.strip(),
            api_key=s.openai_api_key.strip(),
            model=s.openai_model.strip(),
            timeout=timeout,
        )
    return None


def resolve_model(settings: Settings | None = None, task: str = TASK_DEFAULT) -> str:
    """Model id for ``task``: env override > provider default > legacy model.

    Never raises: an unconfigured provider still returns the legacy
    ``openai_model`` so logging/diagnostics can print a sensible name; the
    actual call then fails in ``AIService._chat`` with ``AIServiceError``.
    """
    s = settings or get_settings()
    field = TASK_SETTINGS_FIELDS.get(task)
    if field:
        override = str(getattr(s, field, "") or "").strip()
        if override:
            return override
    provider = resolve_provider(s)
    if provider is not None:
        return provider.model
    return s.openai_model


def build_client_kwargs(provider: ProviderSpec) -> dict[str, Any]:
    """Kwargs for ``AsyncOpenAI(...)`` (no import here; callers own the SDK)."""
    kwargs: dict[str, Any] = {"api_key": provider.api_key, "timeout": provider.timeout}
    if provider.base_url:
        kwargs["base_url"] = provider.base_url
    headers = provider_headers(provider)
    if headers:
        kwargs["default_headers"] = headers
    return kwargs


def provider_headers(provider: ProviderSpec) -> dict[str, str]:
    """Optional request headers implied by the provider config.

    ``x-cmd-zdr: 1`` is Command Code's per-request zero-data-retention switch.
    It is opt-in because some free models (beam/glyph) cannot run under ZDR —
    the gateway hard-fails instead of degrading — so enabling it globally also
    requires pinning the model to a ZDR-capable one.
    """
    if provider.name == "commandcode" and provider.zdr:
        return {"x-cmd-zdr": "1"}
    return {}


def mask_secret(secret: str) -> str:
    """``abcd12...wxyz``-style masking so logs/diagnostics never carry a key.

    The example here is deliberately **not** a real key: a docstring that shows
    a live prefix/suffix leaks those bytes into the repo (and into every clone
    and CI log) even though the key itself is never written down.
    """
    value = (secret or "").strip()
    if len(value) <= 10:
        return "***" if value else ""
    return f"{value[:6]}...{value[-4:]}"


# ---------------------------------------------------------------------------
# Live model list (catalog audit — not an inference call)
# ---------------------------------------------------------------------------


def model_spec_from_payload(item: dict[str, Any]) -> ModelSpec:
    """Map one ``GET /models`` entry to a ``ModelSpec``.

    Unknown ids stay free-flagged by their suffix and carry no catalog extras;
    curated ids inherit ZDR / daily-limit / source facts.
    """
    model_id = str(item.get("id") or "").strip()
    curated = catalog_lookup(model_id)
    if curated is not None:
        return curated
    context_window = item.get("context_length")
    return ModelSpec(
        id=model_id,
        name=str(item.get("name") or ""),
        context_window=int(context_window) if isinstance(context_window, int) else 0,
        free=is_free_model_id(model_id),
        source="live /models",
    )


async def list_remote_models(provider: ProviderSpec) -> list[ModelSpec]:
    """Fetch the provider's model list (``GET {base_url}/models``).

    Raises ``httpx.HTTPError`` on transport/HTTP failure; callers decide whether
    that is fatal (the ops script prints it and exits non-zero).
    """
    import httpx  # local import: keeps this module free of a hard network dependency

    headers = {"Authorization": f"Bearer {provider.api_key}"}
    headers.update(provider_headers(provider))
    async with httpx.AsyncClient(timeout=provider.timeout) as client:
        resp = await client.get(provider.models_url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return []
    return [model_spec_from_payload(item) for item in data if isinstance(item, dict)]


def audit_free_catalog(remote: list[ModelSpec]) -> dict[str, list[str]]:
    """Compare the curated free catalog with the live model list.

    Returns ``{"missing": [...], "uncatalogued_free": [...]}``: curated free
    models the gateway no longer serves (a withdrawn promo, so the default model
    must change) and free-marked ids that are served but not catalogued.
    """
    remote_ids = {spec.id for spec in remote}
    remote_free = {spec.id for spec in remote if spec.free}
    curated = set(free_model_ids())
    return {
        "missing": sorted(curated - remote_ids),
        "uncatalogued_free": sorted(remote_free - curated),
    }


def provider_summary(settings: Settings | None = None) -> dict[str, Any]:
    """Diagnostics for logs and the ops script — never includes the raw key."""
    s = settings or get_settings()
    provider = resolve_provider(s)
    if provider is None:
        return {"configured": False, "reason": "no COMMANDCODE_API_KEY / OPENAI_API_KEY"}
    return {
        "configured": True,
        "provider": provider.name,
        "api": provider.api,
        "base_url": provider.base_url,
        "api_key": mask_secret(provider.api_key),
        "model": provider.model,
        "timeout_seconds": provider.timeout,
        "zdr": provider.zdr,
        "tasks": {task: resolve_model(s, task) for task in TASK_SETTINGS_FIELDS},
        "free_models": free_model_ids(),
    }

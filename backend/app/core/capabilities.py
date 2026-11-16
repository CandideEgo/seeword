"""Runtime capability gates; disabling models never weakens authentication."""

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError


def require_llm() -> None:
    if not get_settings().llm_enabled:
        raise ServiceUnavailableError("模型能力已关闭（LLM_ENABLED=false）")


def require_content_production(*, model: bool = False) -> None:
    if not get_settings().content_production_enabled:
        raise ServiceUnavailableError("内容生产能力已关闭（CONTENT_PRODUCTION_ENABLED=false）")
    if model:
        require_llm()

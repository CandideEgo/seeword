"""Shared, deny-by-default resource policy for delegated learning use cases."""

from app.core.errors import AppError, ErrorCode
from app.services.teaching.principal import Principal, require_scope


def allowed_lesson_ids(principal: Principal) -> frozenset[str] | None:
    """None means the first-party surface; an external empty set grants nothing."""
    if principal.actor == "user_ui":
        return None
    if principal.actor != "external_agent":
        raise AppError(403, "INSUFFICIENT_SCOPE", "此入口仅供本人或获委托连接使用")
    return frozenset(principal.resource_limits.get("lesson_ids", []))


def require_lesson(principal: Principal, lesson_id: str, *, scope: str = "materials:read", write: bool = False) -> None:
    require_scope(principal, scope, write=write)
    allowed = allowed_lesson_ids(principal)
    if allowed is not None and lesson_id not in allowed:
        # A caller's invented ID must not become a resource-existence oracle.
        raise AppError(404, ErrorCode.NOT_FOUND, "学习资源不存在或未获授权")


def required_uses(principal: Principal, *, model: bool = False) -> tuple[str, ...]:
    if model and principal.actor == "external_agent" and principal.disclosure_audience == "application":
        raise AppError(403, "INSUFFICIENT_SCOPE", "此连接未授权向模型披露学习数据")
    uses = ["site_display"]
    if principal.actor == "external_agent":
        uses.append("external_redistribution")
    if model or (principal.actor == "external_agent" and principal.disclosure_audience != "application"):
        uses.append("model_processing")
    return tuple(uses)

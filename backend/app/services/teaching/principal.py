"""Server-derived identity shared by HTTP, model reads and MCP adapters."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from app.core.errors import AppError

DisclosureAudience = Literal["model", "application"]


@dataclass(frozen=True)
class Principal:
    user_id: str
    actor: str = "user_ui"
    request_id: str = ""
    connection_id: str | None = None
    granted_scopes: frozenset[str] = field(default_factory=frozenset)
    credential_issued_at: datetime | None = None
    # Server-loaded, explicit grants for the new learning surface. Legacy
    # teaching credentials gain no course/word rights from an omitted limit.
    resource_limits: dict[str, list[str]] = field(default_factory=dict)
    disclosure_audience: DisclosureAudience = "model"

    @property
    def namespace(self) -> str:
        return f"mcp:{self.connection_id}" if self.actor == "external_agent" else "web"


def require_scope(principal: Principal, scope: str, *, write=False) -> None:
    if principal.actor not in {"user_ui", "internal_agent", "external_agent", "system"}:
        raise AppError(403, "INSUFFICIENT_SCOPE", "无效的调用身份")
    if write and principal.actor in {"internal_agent", "system"}:
        raise AppError(403, "INSUFFICIENT_SCOPE", "模型不能代替用户执行教学动作")
    if principal.actor == "external_agent" and (not principal.connection_id or scope not in principal.granted_scopes):
        raise AppError(403, "INSUFFICIENT_SCOPE", "连接没有该操作的授权")

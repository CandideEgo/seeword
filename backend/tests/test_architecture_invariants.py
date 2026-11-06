"""Mechanized architecture invariants.

Each test names the invariant it protects — the rule text lives in `.agent/invariants.md`. The
point of putting them in code is that reintroducing a removed shape of the system fails a test
instead of passing review because a reviewer did not remember.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

from app.core.database import Base
from app.core.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from app.main import app

STATE_CHANGING = {"POST", "PUT", "PATCH", "DELETE"}
VIDEO_PREFIX = "/api/v1/videos"
API_DIR = Path(__file__).resolve().parent.parent / "app" / "api"
# State-changing video routes that belong to the *user*, not to content management. They must
# still require a logged-in user (see the second test) — they just do not need admin rights.
# Anything that creates or mutates video content must NOT be listed here.
USER_SIDE_ENGAGEMENT: dict[str, str] = {
    f"{VIDEO_PREFIX}/{{video_id}}/like": "a user's own like",
    f"{VIDEO_PREFIX}/{{video_id}}/favorite": "a user's own favorite",
    f"{VIDEO_PREFIX}/{{video_id}}/note": "a user's own note on a video (UserNote, scoped by user_id)",
}


def _dependency_names(dependant) -> set[str]:
    names: set[str] = set()
    stack = [dependant]
    while stack:
        dependency = stack.pop()
        name = getattr(dependency.call, "__name__", "")
        if name:
            names.add(name)
        stack.extend(dependency.dependencies)
    return names


def _all_routes() -> list:
    """Every route the app serves, as objects carrying `path`, `methods`, `dependant`.

    Not `app.routes`: FastAPI 0.141 wraps `include_router` in an `_IncludedRouter`
    that is itself pathless and holds the real routes inside it, so reading
    `route.path` off `app.routes` sees only the handful registered directly
    (`/health`, `/metrics`, the docs). Every check below that walks routes then
    inspects zero of them and passes regardless — 2026-10-16 found the four
    route checks in this file in exactly that state, three of them since the
    FastAPI upgrade. `effective_candidates()` returns the resolved route
    context: full path (prefix included), methods, and `dependant`.
    """
    routes: list = []
    for route in app.routes:
        candidates = getattr(route, "effective_candidates", None)
        if callable(candidates):
            routes.extend(candidates())
        else:
            routes.append(route)
    return routes


def _route_paths() -> list[str]:
    return [str(getattr(route, "path", "")) for route in _all_routes()]


def _state_changing_video_routes() -> list[tuple[str, set[str], set[str]]]:
    found = []
    for route in _all_routes():
        methods = set(getattr(route, "methods", set()) or set()) & STATE_CHANGING
        path = getattr(route, "path", "")
        if methods and path.startswith(VIDEO_PREFIX):
            found.append((path, methods, _dependency_names(route.dependant)))
    return found


class TestVideoProcessingIsOperatorTriggered:
    """INV-003: video processing is admin/catalog-triggered only — there is no user submit path."""

    def test_state_changing_video_routes_require_admin(self):
        """Every mutation of video content is admin-guarded.

        A new unguarded mutation fails here. If a route is legitimately user-side, add it to
        USER_SIDE_ENGAGEMENT with a reason rather than loosening this test.
        """
        routes = _state_changing_video_routes()
        # A guard on the guard: an enumeration that finds nothing passes every
        # assertion below without inspecting a single route (see _all_routes).
        assert routes, "found no state-changing video routes at all — the walk is broken, not the app"
        unguarded = [
            (path, sorted(methods))
            for path, methods, dependencies in routes
            if path not in USER_SIDE_ENGAGEMENT and "get_admin_user" not in dependencies
        ]
        assert not unguarded, f"state-changing video routes without admin auth: {unguarded}"

    def test_user_side_video_routes_require_a_logged_in_user(self):
        """The user-side exceptions are still authenticated, not open."""
        unauthenticated = [
            path
            for path, _, dependencies in _state_changing_video_routes()
            if path in USER_SIDE_ENGAGEMENT and "get_current_user" not in dependencies
        ]
        assert not unauthenticated, f"user-side video routes with no auth at all: {unauthenticated}"

    def test_no_bare_post_videos_route(self):
        """`POST /api/v1/videos` was the user submit-URL endpoint — removed in DEC-025."""
        registered = {
            (method, str(getattr(route, "path", "")))
            for route in _all_routes()
            for method in (getattr(route, "methods", set()) or set())
        }
        assert ("POST", VIDEO_PREFIX) not in registered

    @pytest.mark.parametrize(
        "fragment",
        ["/upload", "/fork", "/propose", "/begin-edit", "/submit-review", "/user-seed"],
    )
    def test_removed_submission_routes_stay_removed(self, fragment):
        """DEC-025 removed the user submission surface; none of it may reappear."""
        offenders = [path for path in _route_paths() if fragment in path]
        assert not offenders, f"removed '{fragment}' routes reappeared: {offenders}"


# --- error contract (docs/architecture-fix-plan-2026-10.md 批 1) -------------

# 服务层过去用这些内建异常表达领域失败，路由层再按消息文本反解状态码。
LEGACY_DOMAIN_EXC_TYPES = {"ValueError", "LookupError", "PermissionError"}

# 表达式形态的"异常消息文本"，任何对它做子串/大小写判断的地方都是散文决定状态码。
_EXC_MESSAGE_EXPR = r"(?:msg|message|str\(\s*(?:e|exc|err|ex|error)\s*\))"
_MESSAGE_SNIFFING_PATTERNS = (
    re.compile(rf"\b(?:in|not\s+in)\s+{_EXC_MESSAGE_EXPR}"),
    re.compile(rf"{_EXC_MESSAGE_EXPR}\s*\.\s*(?:lower|casefold)\s*\("),
    re.compile(rf"{_EXC_MESSAGE_EXPR}\s*(?:==|!=)\s*"),
)


def _api_python_files() -> list[Path]:
    return sorted(API_DIR.rglob("*.py"))


def _source_without_comments(path: Path) -> list[str]:
    """The file's lines with `#` comments blanked out (line numbers preserved).

    Comments are documentation, not behaviour: `test_no_message_sniffing` must
    not fire on a comment that *describes* the pattern it bans.
    """
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            (start_row, start_col), (end_row, end_col) = token.start, token.end
            if start_row == end_row:
                line = lines[start_row - 1]
                lines[start_row - 1] = line[:start_col] + " " * (end_col - start_col) + line[end_col:]
    except tokenize.TokenError:
        pass  # a file we cannot tokenize is still scanned, comments and all
    return lines


def _try_body_of_except(lines: list[str], except_index: int) -> list[str]:
    """The `try:` block governed by the `except` at ``except_index``.

    Scans backwards for the `try:` at the same indentation — enough for the
    flat try/except shapes this codebase uses, and a miss (no `try:` found)
    simply collects into the enclosing block, which only makes the check
    noisier, never silently permissive.
    """
    indent = len(lines[except_index]) - len(lines[except_index].lstrip())
    collected: list[str] = []
    for line in reversed(lines[:except_index]):
        if not line.strip():
            collected.append(line)
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent < indent or (line_indent == indent and line.lstrip().startswith("try:")):
            break
        collected.append(line)
    return list(reversed(collected))


def _enclosing_except_block(lines: list[str], index: int) -> list[str]:
    """Lines of the `except` block that governs ``lines[index]`` (empty if none).

    Used to ask "does the thing that inspects this message also choose a
    response status?" rather than "was a message inspected at all" — see
    `test_no_message_sniffing`.
    """
    indent = len(lines[index]) - len(lines[index].lstrip())
    start = None
    for candidate in range(index - 1, -1, -1):
        if not lines[candidate].strip():
            continue
        candidate_indent = len(lines[candidate]) - len(lines[candidate].lstrip())
        if candidate_indent < indent and lines[candidate].lstrip().startswith("except"):
            start = candidate
            break
    if start is None:
        return []
    block_indent = len(lines[start]) - len(lines[start].lstrip())
    block: list[str] = []
    for line in lines[start:]:
        if not line.strip():
            block.append(line)
            continue
        if block and len(line) - len(line.lstrip()) <= block_indent:
            break
        block.append(line)
    return block


_STATUS_DECIDING_RAISE = re.compile(r"(?:HTTPException|AppError)\s*\(|raise\s+\w*Error\s*\(")


class TestErrorsAreTypesNotProse:
    """批 1b/1c: domain failures are types, so no status code is derived from wording."""

    def test_no_message_sniffing(self):
        """No status code may be chosen by matching the text of an exception message.

        `if "not found" in msg.lower()` (16 sites in videos.py before 批 1c) made
        the status a function of an English substring: reword the message, or
        translate it, and the 404 silently becomes a 500.

        Only message inspection that feeds a response status counts. `auth.py`
        and `learning.py` also match on exception text, but they match a
        **database constraint name** to recover from a concurrent-insert race
        (then re-fetch and answer 200) — no status is derived from prose there,
        and those handlers are deliberately left alone.
        """
        offenders = []
        for path in _api_python_files():
            lines = _source_without_comments(path)
            for index, line in enumerate(lines):
                if not any(pattern.search(line) for pattern in _MESSAGE_SNIFFING_PATTERNS):
                    continue
                block = _enclosing_except_block(lines, index)
                if any(_STATUS_DECIDING_RAISE.search(candidate) for candidate in block):
                    offenders.append(f"{path.relative_to(API_DIR.parent.parent)}:{index + 1}: {line.strip()}")
        assert not offenders, "status codes decided by exception prose:\n" + "\n".join(offenders)

    def test_no_router_recatches_service_errors_by_builtin_type(self):
        """A router must not wrap a service call in `except ValueError` (etc.).

        Services raise `DomainError` subclasses, which carry their own status
        code and reach the global handler directly. The two `except ValueError`
        blocks in `api/v1/media.py` are local parsing (`Path.relative_to`, the
        Range header's `int()`) with no service call in the try body, so this
        rule leaves them alone.
        """
        offenders = []
        for path in _api_python_files():
            lines = path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                match = re.match(r"\s*except\s+(\w+)", line)
                if match is None or match.group(1) not in LEGACY_DOMAIN_EXC_TYPES:
                    continue
                body = "\n".join(_try_body_of_except(lines, index))
                if "service" in body:
                    offenders.append(f"{path.name}:{index + 1}: except {match.group(1)} wraps a service call")
        assert not offenders, "routers re-decide service error status codes:\n" + "\n".join(offenders)


class TestDomainErrorStatusCodes:
    """The mapping service -> HTTP lives in the class, not in a router.

    Changing a row here is changing the API contract; `tests/test_response_contract.py`
    pins what the wire actually looks like.
    """

    @pytest.mark.parametrize(
        ("exc_type", "expected_status", "expected_code"),
        [
            (NotFoundError, 404, "NOT_FOUND"),
            (BadRequestError, 400, "BAD_REQUEST"),
            (ForbiddenError, 403, "FORBIDDEN"),
            (ConflictError, 409, "CONFLICT"),
            (ServiceUnavailableError, 503, "SERVICE_UNAVAILABLE"),
        ],
    )
    def test_subclass_status_and_code(self, exc_type, expected_status, expected_code):
        exc = exc_type("boom")
        assert exc.status_code == expected_status
        assert exc.code == expected_code
        assert exc.message == "boom"

    def test_every_domain_error_is_an_app_error(self):
        """Inheritance is what keeps the global handler from needing a branch per subclass."""
        for exc_type in (NotFoundError, BadRequestError, ForbiddenError, ConflictError, ServiceUnavailableError):
            assert issubclass(exc_type, AppError)


# --- 批 1d: 鉴权只有一条校验链 ----------------------------------------------

DEPENDENCIES_PATH = API_DIR / "dependencies.py"


def _called_names(node: ast.AST) -> set[str]:
    return {call.func.id for call in ast.walk(node) if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)}


class TestAuthenticationHasOneChain:
    """批 1d: `get_current_user` 与 `get_optional_user` 共用一条校验链。

    它们曾经是同一段逻辑的两份拷贝（token 类型、黑名单、`password_changed_at`、
    用户是否还在、是否被封禁），只在最后一步分叉成 `raise` 与 `return None`。
    代价不是重复本身，而是**加规则要改两处且漏一处不报错**：可选鉴权端点会静默
    地少一道门，而没有测试会因此变红。

    这里用源码级断言把「不许再长出第二份」变成会失败的东西——和本文件其余检查
    同一路数。它只断言"派发到共享链"，不断言链里有哪些规则（那是
    `dependencies.py::_authenticate` 的事）。
    """

    def test_token_validation_lives_in_exactly_one_function(self):
        """`decode_token` 在 dependencies.py 里只许出现在 `_authenticate` 中。"""
        tree = ast.parse(DEPENDENCIES_PATH.read_text(encoding="utf-8"))
        holders = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and "decode_token" in _called_names(node)
        ]
        assert holders == ["_authenticate"], f"token 解码出现在 {holders} —— 鉴权链被复制了"

    def test_both_dependencies_delegate_to_the_shared_chain(self):
        tree = ast.parse(DEPENDENCIES_PATH.read_text(encoding="utf-8"))
        dependencies = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name in {"get_current_user", "get_optional_user"}
        }
        assert sorted(dependencies) == ["get_current_user", "get_optional_user"]
        for name, node in dependencies.items():
            assert "_authenticate" in _called_names(node), f"{name} 绕过了 _authenticate"


# --- 批 5: 被砍掉的三个特性不许留下化石 --------------------------------------

# 六张表属于三个已被砍掉的功能：YouTube 评论质量分析（随社区/UGC 层一起砍，
# ADR-0012）、fork→standard 的「回提 PR」流程（Phase 3e）、每日学习计划派发
# （2026-08-27 砍）。功能删了，模型和表留着——于是每次基于 `create_all` 的测试
# 都要建它们，每个 autogenerate diff 都要绕开它们。表在迁移 `d1e2f3a4b5c6` 里删掉，
# 这个测试守的是另一半：别再长出声明同名的模型。
#
# 2026-10 审计又清掉一批（券码系统、冻结的口语评测、跟读/周报、练习题缓存），
# 表在迁移 `c3d4e5f6a7b8` 里删除；同样不允许模型复活它们。
DROPPED_TABLES = frozenset(
    {
        "video_comments",
        "video_comment_stats",
        "subtitle_change_proposals",
        "subtitle_mergeable_updates",
        "learning_plans",
        "learning_plan_items",
        # 2026-10 backend cleanup (migration c3d4e5f6a7b8)
        "redeem_codes",
        "speaking_attempts",
        "speaking_rubrics",
        "rubric_criteria",
        "speaking_attempt_scores",
        "shadowing_attempts",
        "weekly_reports",
        "video_practice_questions",
        # 2026-11 paid-membership chain removal (migration d4e5f6a7b8c9)
        "orders",
        "jinshuju_payments",
        "user_video_unlocks",
    }
)

# 学习计划派发删掉后，这五条路由先用 410 Gone 过渡了一段时间，现在连桩也不留。
# 片段比较（而不是整段相等）是刻意的：`/plan/profile` 这类活路由与它们不共享片段。
REMOVED_PLAN_ROUTE_FRAGMENTS = (
    "/plan/today",
    "/plan/progress",
    "/plan/history",
    "/plan/items/",
    "/plan/generate/",
)

# 2026-11 下线会员收费链路：收款、订单、解锁端点与后台付费记录都不许复活。
REMOVED_PAYMENT_ROUTE_FRAGMENTS = (
    "/payments",
    "/videos/{video_id}/unlock",
    "/videos/unlocked",
    "/admin/payments",
    "/admin/users/{user_id}/plan",
)


class TestCutFeaturesStayCut:
    """批 5: 被砍功能的表与路由都不许复活。

    `Base.metadata` 是「表还在」的判据；路由表是「接口还在」的判据。两者都不会
    因为某个功能的业务代码被删而自动收缩——正是这一点让它们活过了自己的功能。
    """

    def test_no_model_declares_a_dropped_table(self):
        import app.models  # noqa: F401  (导入即注册全部模型)

        resurrected = sorted(DROPPED_TABLES & set(Base.metadata.tables))
        assert not resurrected, f"已删的表又出现在 Base.metadata 里：{resurrected}"

    @pytest.mark.parametrize("fragment", REMOVED_PLAN_ROUTE_FRAGMENTS)
    def test_removed_plan_routes_stay_removed(self, fragment):
        offenders = [path for path in _route_paths() if fragment in path]
        assert not offenders, f"已删的 '{fragment}' 路由又出现了：{offenders}"


def test_services_and_tasks_do_not_import_http_adapters():
    """Business transactions and worker entry points must not depend on routes."""
    app_dir = API_DIR.parent
    files = [path for layer in ("services", "tasks") for path in (app_dir / layer).rglob("*.py")]
    assert files, "architecture scan found no application services/tasks"
    offenders = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
                if node.module == "app":
                    modules.extend(f"app.{name.name}" for name in node.names)
            elif isinstance(node, ast.Import):
                modules = [name.name for name in node.names]
            if any(name == "app.api" or name.startswith("app.api.") for name in modules):
                offenders.append(f"{path.relative_to(app_dir)}:{node.lineno}")
    assert not offenders, f"services/tasks import HTTP adapters: {offenders}"

    @pytest.mark.parametrize("fragment", REMOVED_PAYMENT_ROUTE_FRAGMENTS)
    def test_removed_payment_routes_stay_removed(self, fragment):
        offenders = [path for path in _route_paths() if fragment in path]
        assert not offenders, f"已下线会员收费链路的端点又出现了：{offenders}"


def test_model_chat_endpoint_lives_in_exactly_one_module():
    """INV: every model completion request goes through ``teaching_gateway``.

    ``TID251`` bans importing provider SDKs outside the service layer; this
    pins the other half: hand-rolled HTTP to an OpenAI-compatible endpoint must
    not grow a second home (and with it a second budget/cap path).
    """
    app_root = Path(__file__).resolve().parent.parent / "app"
    offenders = [
        str(path.relative_to(app_root))
        for path in app_root.rglob("*.py")
        if path.name != "teaching_gateway.py" and '"/chat/completions"' in path.read_text(encoding="utf-8")
    ]
    assert offenders == []

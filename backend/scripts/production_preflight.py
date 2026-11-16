#!/usr/bin/env python
"""生产配置预检（A11 / OPS-07）——不连库、不建容器，只验证「会不会带着错配置上线」。

覆盖三类真实事故：

1. **弱密钥/缺密钥**：``ENV=production`` 下缺 ``JWT_SECRET`` 或短于 32 字符必须
   启动失败（空密钥曾让任何人可伪造 token）。
2. **生产开了开发假短信**：``SMS_DEV_FAKE_ENABLED=true`` 在生产必须拒绝启动
   （固定码 1234 能登进任何手机号）。
3. **配置白名单漂移**：``docker-compose.prod.yml`` 必须把告警/Sentry 变量透传进
   容器（A09 修过一次：宿主 .env 写了也进不了容器）；``nginx.ssl.conf`` 必须仍带
   CSP ``media-src`` 与 HSTS。

用法（CI 或本机）::

    python backend/scripts/production_preflight.py

失败即非零退出；每步打印实际命令与关键输出，不把「跑不了」写成通过。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

#: 故意不完整的生产环境：缺 JWT_SECRET / DATABASE_URL / REDIS_URL / 回调密钥。
BASE_ENV = {
    "ENV": "production",
    "PYTHONUTF8": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
}

VALID_SECRETS = {
    "JWT_SECRET": "production_preflight_secret_at_least_32_chars",
    "DATABASE_URL": "postgresql+asyncpg://preflight:preflight@127.0.0.1:65432/preflight",
    "REDIS_URL": "redis://127.0.0.1:65439/0",
    "TRANSCRIPTION_CALLBACK_SECRET": "preflight-callback-secret",
    "OPENAI_API_KEY": "sk-preflight-placeholder",
}


def _run_settings(extra_env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """在临时目录里跑 Settings()——避开 backend/.env，只吃我们给的环境变量。"""
    # 复制完整环境再覆盖：Windows 上丢掉 SystemRoot/PATH 会让 winsock 初始化失败
    # （导入 asyncio 时 OSError 10106），看起来像「配置被拒绝」，实际是环境坏了。
    env = {**os.environ, **BASE_ENV, **extra_env}
    for key in ("JWT_SECRET", "DATABASE_URL", "REDIS_URL", "TRANSCRIPTION_CALLBACK_SECRET", "OPENAI_API_KEY"):
        if key not in extra_env:
            env.pop(key, None)
    with tempfile.TemporaryDirectory() as tmpdir:
        return subprocess.run(
            [sys.executable, "-c", "from app.core.config import Settings; Settings()"],
            cwd=tmpdir,
            env={**env, "PYTHONPATH": str(BACKEND_ROOT)},
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )


def _expect_failure(label: str, extra_env: dict[str, str], needle: str) -> list[str]:
    result = _run_settings(extra_env)
    problems: list[str] = []
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode == 0:
        problems.append(f"{label}：生产配置本应启动失败，实际加载成功")
    elif needle not in output:
        problems.append(f"{label}：失败原因里没有 {needle!r}，看到的输出：{output.strip()[-400:]}")
    else:
        print(f"PASS {label}: exit {result.returncode}，拒绝原因包含 {needle!r}")
    return problems


def _expect_success(label: str, extra_env: dict[str, str]) -> list[str]:
    result = _run_settings(extra_env)
    if result.returncode != 0:
        return [
            f"{label}：合法的生产配置被拒绝（exit {result.returncode}）：{(result.stdout + result.stderr).strip()[-600:]}"
        ]
    print(f"PASS {label}")
    return []


def _check_file_contains(path: Path, needles: list[str]) -> list[str]:
    if not path.is_file():
        return [f"{path} 不存在"]
    text = path.read_text(encoding="utf-8")
    problems = [f"{path.name} 缺少 {needle!r}" for needle in needles if needle not in text]
    if not problems:
        print(f"PASS {path.relative_to(REPO_ROOT)} 包含 {len(needles)} 个必要项")
    return problems


def main() -> int:
    problems: list[str] = []

    problems += _expect_failure("缺 JWT_SECRET", {}, "JWT_SECRET")
    problems += _expect_failure(
        "短 JWT_SECRET",
        {**VALID_SECRETS, "JWT_SECRET": "too-short"},
        "JWT_SECRET",
    )
    problems += _expect_failure(
        "缺 DATABASE_URL",
        {**VALID_SECRETS, "DATABASE_URL": ""},
        "DATABASE_URL",
    )
    problems += _expect_failure(
        "生产启用假短信",
        {**VALID_SECRETS, "SMS_DEV_FAKE_ENABLED": "true"},
        "SMS_DEV_FAKE_ENABLED",
    )
    problems += _expect_success("最小合法生产配置", VALID_SECRETS)

    # A09 回归：告警/Sentry 变量必须在生产 compose 的白名单里，否则宿主 .env
    # 写了也进不了容器，事故发生时没有任何站外告警。
    problems += _check_file_contains(
        REPO_ROOT / "docker-compose.prod.yml",
        ["SENTRY_DSN", "ALERT_WEBHOOK_URL", "ALERT_WEBHOOK_SECRET"],
    )
    # Same failure mode as A09, for the SLCS pilot: the switches are read from
    # Settings, but a name that is not listed in the prod compose whitelist
    # never reaches the container, so "打开开关" would silently do nothing.
    problems += _check_file_contains(
        REPO_ROOT / "docker-compose.prod.yml",
        [
            "SLCS_LESSONS_ENABLED",
            "SLCS_TUTOR_ENABLED",
            "SLCS_VOCABULARY_ENABLED",
            "SLCS_LESSON_RECEIPT_ISSUER",
            "SLCS_LESSON_RECEIPT_PUBLIC_KEYS",
            "SLCS_LESSON_RECEIPT_MAX_AGE_SECONDS",
        ],
    )
    problems += _check_file_contains(
        REPO_ROOT / "nginx.ssl.conf",
        ["Content-Security-Policy", "media-src 'self' blob:", "Strict-Transport-Security"],
    )

    if problems:
        print("\n::error::生产配置预检未通过：")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\n生产配置预检通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

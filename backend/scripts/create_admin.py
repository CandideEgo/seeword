"""由运营者创建密码账号（默认管理员，--role user 创建普通账号）。

无默认密码、无短信固定码。建议 --prompt-password，避免命令行历史泄露；
兼容 ADMIN_PHONE / ADMIN_PASSWORD 和既有 --reset-password。
已有账号默认只可提升为管理员；--role user 永不降级管理员。
此脚本只连显式配置的库，不迁移数据库。执行前先核对 DATABASE_URL。
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_async_session_maker
from app.core.security import hash_password, validate_password_strength
from app.models.user import RoleType, User
from app.schemas.user import SendSmsCodeRequest


def validate_inputs(phone: str, password: str | None, reset: bool) -> None:
    # Share the API's phone pattern and new-password contract, never truncate.
    SendSmsCodeRequest(phone=phone)
    if password is not None:
        validate_password_strength(password)
    if reset and password is None:
        raise ValueError("--reset-password 必须提供新密码")


async def _create_or_promote(phone: str, password: str | None, reset: bool, *, role: RoleType = RoleType.admin) -> None:
    validate_inputs(phone, password, reset)
    if "database_url" not in get_settings().model_fields_set:
        raise ValueError("必须显式配置 DATABASE_URL，拒绝使用开发库回退")
    async with get_async_session_maker()() as db:
        result = await db.execute(select(User).where(User.phone == phone).with_for_update())
        user = result.scalar_one_or_none()
        if user is None:
            if password is None:
                raise ValueError("新账号必须提供密码（推荐 --prompt-password）")
            user = User(
                phone=phone,
                hashed_password=hash_password(password),
                name="Admin" if role == RoleType.admin else None,
                role=role,
                onboarding_completed=role == RoleType.admin,
            )
            db.add(user)
            await db.commit()
            print(f"Created {role.value} user: {phone}")
            return

        if user.is_banned or user.deletion_requested_at is not None:
            raise ValueError("禁止修改已封禁或注销冷静期账号；请走独立恢复流程")
        changed = False
        if role == RoleType.admin and user.role != RoleType.admin:
            user.role = RoleType.admin
            changed = True
        if reset:
            # Reset invalidates all older sessions, just like the HTTP endpoint.
            user.hashed_password = hash_password(password)
            user.password_changed_at = datetime.now(UTC)
            changed = True
        if changed:
            await db.commit()
            print(f"Updated account: {phone}")
        else:
            print(f"Account already exists: {phone}; no changes (--reset-password to reset).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phone", default=os.environ.get("ADMIN_PHONE"), help="手机号（或 ADMIN_PHONE）")
    parser.add_argument("--role", choices=[r.value for r in RoleType], default="admin")
    passwords = parser.add_mutually_exclusive_group()
    passwords.add_argument("--password", help="密码；推荐改用 --prompt-password")
    passwords.add_argument("--prompt-password", action="store_true", help="交互输入，不写入命令行历史")
    parser.add_argument("--reset-password", action="store_true")
    args = parser.parse_args()
    if not args.phone:
        parser.error("必须提供 --phone 或 ADMIN_PHONE")
    password = args.password if args.password is not None else os.environ.get("ADMIN_PASSWORD")
    if args.prompt_password:
        password = getpass.getpass("Password: ")
        if password != getpass.getpass("Repeat password: "):
            parser.error("两次密码不一致")
    try:
        asyncio.run(_create_or_promote(args.phone, password, args.reset_password, role=RoleType(args.role)))
    except ValueError:
        # Pydantic errors may echo input values; do not print the exception.
        parser.error(
            "输入无效：手机号须符合站内格式，密码至少8位且含大小写/数字、最多72 UTF-8字节；新建/重置须给密码，封禁/注销账号不可修改"
        )


if __name__ == "__main__":
    main()

"""Grant or revoke a user's access to the V2 teaching surfaces.

``TeachingAccessGrant`` is the durable allowlist row that ``v2_access`` checks
after the feature flags. Until now nothing in the product wrote it — the only
path was the ``TEACHING_ALLOWED_USER_IDS`` env list, which cannot be changed
without a restart and is awkward for a private beta. This script is the
missing write path; it deliberately stays outside the HTTP API so no user can
grant themselves teaching access.

Usage (working directory ``backend/``, Windows needs ``PYTHONUTF8=1``):

    python scripts/grant_teaching_access.py --phone 13900009991
    python scripts/grant_teaching_access.py --phone 13900009991 --revoke
    python scripts/grant_teaching_access.py --list

Exits 0 on success, 1 on usage / lookup error.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Run as `python scripts/<name>.py` from `backend/`: that puts `scripts/`
# on sys.path, not the backend root, so `app.*` would not resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.database import async_session
from app.models.user import User
from app.models.v2_runtime import TeachingAccessGrant


async def _user(db, phone: str) -> User:
    user = await db.scalar(select(User).where(User.phone == phone))
    if user is None:
        raise LookupError(f"没有手机号为 {phone} 的账号")
    return user


async def _grant(phone: str, revoke: bool) -> int:
    async with async_session() as db:
        user = await _user(db, phone)
        existing = await db.get(TeachingAccessGrant, user.id)
        if revoke:
            if existing is None:
                print(f"{phone} 本来就没有教学授权，无需撤销")
                return 0
            await db.delete(existing)
            await db.commit()
            print(f"已撤销 {phone}（{user.id}）的教学授权")
            return 0
        if existing is not None:
            print(f"{phone}（{user.id}）已有教学授权，无需重复写入")
            return 0
        db.add(TeachingAccessGrant(user_id=user.id))
        await db.commit()
        print(f"已授予 {phone}（{user.id}）教学授权")
        return 0


async def _list() -> int:
    async with async_session() as db:
        rows = (
            await db.execute(
                select(TeachingAccessGrant.user_id, User.phone, User.name)
                .join(User, User.id == TeachingAccessGrant.user_id)
                .order_by(TeachingAccessGrant.user_id)
            )
        ).all()
    if not rows:
        print("没有任何教学授权")
        return 0
    for user_id, phone, name in rows:
        print(f"{phone}\t{name or ''}\t{user_id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="授予或撤销 V2 教学访问权限")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phone", help="要授权的手机号")
    group.add_argument("--list", action="store_true", help="列出当前所有授权")
    parser.add_argument("--revoke", action="store_true", help="撤销而不是授予")
    args = parser.parse_args(argv)
    if args.list and args.revoke:
        parser.error("--list 与 --revoke 不能同时使用")
    try:
        if args.list:
            return asyncio.run(_list())
        return asyncio.run(_grant(args.phone, args.revoke))
    except LookupError as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

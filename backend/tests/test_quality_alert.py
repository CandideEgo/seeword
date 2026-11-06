"""Tests for admin quality-alert notifications (阶段 4)."""

import pytest
from sqlalchemy import select

from app.models.notification import Notification
from app.models.user import RoleType, User
from app.services.notification_service import notify_admins


class TestNotifyAdmins:
    @pytest.mark.asyncio
    async def test_notifies_all_admins_only(self, db_session):
        # 2 admins + 1 regular user
        for i, role in enumerate([RoleType.admin, RoleType.admin, RoleType.user]):
            db_session.add(
                User(
                    phone=f"1380000{i}",
                    hashed_password="x",
                    name=f"u{i}",
                    role=role,
                )
            )
        await db_session.commit()

        await notify_admins(db_session, "测试告警", "msg", related_url="/admin/videos/v1")

        rows = (
            (await db_session.execute(select(Notification).where(Notification.type == "quality_alert"))).scalars().all()
        )
        assert len(rows) == 2  # only admins

    @pytest.mark.asyncio
    async def test_dedup_same_related_url_updates(self, db_session):
        db_session.add(
            User(
                phone="1380001",
                hashed_password="x",
                name="admin",
                role=RoleType.admin,
            )
        )
        await db_session.commit()

        await notify_admins(db_session, "t1", "m1", related_url="/admin/videos/v2")
        await notify_admins(db_session, "t2", "m2", related_url="/admin/videos/v2")

        rows = (
            (await db_session.execute(select(Notification).where(Notification.type == "quality_alert"))).scalars().all()
        )
        assert len(rows) == 1  # deduped - updated, not duplicated
        assert rows[0].title == "t2"
        assert rows[0].message == "m2"

    @pytest.mark.asyncio
    async def test_no_admins_no_error(self, db_session):
        """notify_admins with zero admins completes without raising."""
        # No users at all
        await notify_admins(db_session, "t", "m", related_url="/admin/videos/v3")
        rows = (
            (await db_session.execute(select(Notification).where(Notification.type == "quality_alert"))).scalars().all()
        )
        assert len(rows) == 0

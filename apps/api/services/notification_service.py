"""Notification service: list, mark read."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Notification, User


async def list_for_user(
    db: AsyncSession, user_id: uuid.UUID, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    stmt = (
        select(Notification)
        .options(selectinload(Notification.actor))
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_read(
    db: AsyncSession, user_id: uuid.UUID, notification_ids: list[uuid.UUID] | None = None
) -> int:
    """标记已读。notification_ids=None 表示全部已读。返回影响行数。"""
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(timezone.utc))
    )
    if notification_ids is not None:
        stmt = stmt.where(Notification.id.in_(notification_ids))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0

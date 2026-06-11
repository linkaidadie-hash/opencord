"""Thread service — Open Topic Network.

C 阶段不接 posts / comments；thread 自身就是讨论流条目。
body_html 暂存空字符串，预留给后续 Markdown 渲染管线（不在 C 阶段引入）。
"""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_topic import (
    DEFAULT_TENANT_ID,
    ensure_tenant_exists,
    resolve_tenant_id,
)
from models import Thread, User, Topic


class ThreadServiceError(Exception):
    pass


async def create_thread(
    db: AsyncSession, creator: User, topic_id: uuid.UUID,
    parent_id: uuid.UUID | None, body_md: str,
) -> Thread:
    # 校验 topic 存在
    topic = await db.execute(select(Topic).where(Topic.id == topic_id))
    if topic.scalar_one_or_none() is None:
        raise ThreadServiceError(f"Topic {topic_id} not found")
    if parent_id is not None:
        parent = await db.execute(select(Thread).where(Thread.id == parent_id))
        if parent.scalar_one_or_none() is None:
            raise ThreadServiceError(f"Parent thread {parent_id} not found")
        if (parent.scalar_one()).topic_id != topic_id:
            raise ThreadServiceError("Parent thread belongs to a different topic")

    tenant_id = resolve_tenant_id(creator)
    await ensure_tenant_exists(db, tenant_id)

    thread = Thread(
        tenant_id=tenant_id,
        topic_id=topic_id,
        parent_id=parent_id,
        created_by=creator.id,
        body_md=body_md,
        body_html="",  # 渲染管线不在 C 阶段做
        status="published",
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)
    return thread


async def list_threads_by_topic(
    db: AsyncSession, topic_id: uuid.UUID,
    viewer: User | None = None,
    limit: int = 100, offset: int = 0,
) -> list[Thread]:
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = (
        select(Thread)
        .where(
            Thread.tenant_id == tenant_id,
            Thread.topic_id == topic_id,
            Thread.status != "deleted",
        )
        .order_by(Thread.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_thread_by_id(db: AsyncSession, thread_id: uuid.UUID) -> Thread | None:
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    return result.scalar_one_or_none()


async def delete_thread(db: AsyncSession, thread: Thread) -> None:
    thread.status = "deleted"
    await db.commit()

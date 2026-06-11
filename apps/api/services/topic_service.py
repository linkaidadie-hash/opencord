"""Topic service — Open Topic Network."""
from __future__ import annotations
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_topic import (
    DEFAULT_TENANT_ID,
    ensure_topic_status,
    ensure_tenant_exists,
    resolve_tenant_id,
)
from models import Topic, User, Community


class TopicServiceError(Exception):
    pass


async def create_topic(
    db: AsyncSession, creator: User, community_id: uuid.UUID,
    slug: str, title: str, body_md: str,
) -> Topic:
    community = await db.execute(select(Community).where(Community.id == community_id))
    if community.scalar_one_or_none() is None:
        raise TopicServiceError(f"Community {community_id} not found")

    tenant_id = resolve_tenant_id(creator)
    await ensure_tenant_exists(db, tenant_id)

    existing = await db.execute(
        select(Topic).where(
            Topic.community_id == community_id,
            Topic.slug == slug,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise TopicServiceError(f"Topic slug '{slug}' already exists in this community")

    topic = Topic(
        tenant_id=tenant_id,
        community_id=community_id,
        slug=slug,
        title=title,
        body_md=body_md,
        status="open",
        created_by=creator.id,
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    return topic


async def list_topics(
    db: AsyncSession,
    viewer: User | None = None,
    community_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Topic]:
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = select(Topic).where(Topic.tenant_id == tenant_id)
    stmt = stmt.order_by(Topic.updated_at.desc())
    if community_id:
        stmt = stmt.where(Topic.community_id == community_id)
    if status:
        ensure_topic_status(status)
        stmt = stmt.where(Topic.status == status)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_topic_by_id(db: AsyncSession, topic_id: uuid.UUID) -> Topic | None:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    return result.scalar_one_or_none()


async def get_topic_by_slug(
    db: AsyncSession, community_id: uuid.UUID, slug: str
) -> Topic | None:
    result = await db.execute(
        select(Topic).where(
            Topic.community_id == community_id,
            Topic.slug == slug,
        )
    )
    return result.scalar_one_or_none()


async def update_topic_status(db: AsyncSession, topic: Topic, new_status: str) -> Topic:
    ensure_topic_status(new_status)
    topic.status = new_status
    await db.commit()
    await db.refresh(topic)
    return topic


async def recount_threads(db: AsyncSession, topic_id: uuid.UUID) -> int:
    from models import Thread
    result = await db.execute(
        select(func.count(Thread.id)).where(Thread.id == topic_id)
    )
    count = result.scalar_one()
    topic = await get_topic_by_id(db, topic_id)
    if topic is not None:
        topic.thread_count = count
        await db.commit()
    return count

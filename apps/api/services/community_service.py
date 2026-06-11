"""Community service — Open Topic Network."""
from __future__ import annotations
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_topic import (
    DEFAULT_TENANT_ID,
    ensure_community_visibility,
    ensure_tenant_exists,
    resolve_tenant_id,
)
from models import Community, User


class CommunityServiceError(Exception):
    pass


async def create_community(
    db: AsyncSession, creator: User, slug: str, name: str,
    description: str | None, visibility: str,
) -> Community:
    ensure_community_visibility(visibility)
    tenant_id = resolve_tenant_id(creator)
    await ensure_tenant_exists(db, tenant_id)
    existing = await db.execute(
        select(Community).where(
            Community.tenant_id == tenant_id,
            Community.slug == slug,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise CommunityServiceError(f"Community slug '{slug}' already exists")
    community = Community(
        tenant_id=tenant_id,
        slug=slug,
        name=name,
        description=description,
        visibility=visibility,
        created_by=creator.id,
    )
    db.add(community)
    await db.commit()
    await db.refresh(community)
    return community


async def list_communities(
    db: AsyncSession, viewer: User | None = None,
    visibility: str | None = None, limit: int = 50, offset: int = 0,
) -> list[Community]:
    # 读路径也走 viewer 解析的 tenant；未登录场景用 default
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = select(Community).where(Community.tenant_id == tenant_id)
    stmt = stmt.order_by(Community.topic_count.desc(), Community.created_at.desc())
    if visibility:
        ensure_community_visibility(visibility)
        stmt = stmt.where(Community.visibility == visibility)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_community_by_id(db: AsyncSession, community_id: uuid.UUID) -> Community | None:
    result = await db.execute(select(Community).where(Community.id == community_id))
    return result.scalar_one_or_none()


async def get_community_by_slug(db: AsyncSession, slug: str) -> Community | None:
    tenant_id = uuid.UUID(DEFAULT_TENANT_ID)
    result = await db.execute(
        select(Community).where(
            Community.tenant_id == tenant_id,
            Community.slug == slug,
        )
    )
    return result.scalar_one_or_none()


async def recount_topics(db: AsyncSession, community_id: uuid.UUID) -> int:
    from models import Topic
    result = await db.execute(
        select(func.count(Topic.id)).where(Topic.community_id == community_id)
    )
    count = result.scalar_one()
    community = await get_community_by_id(db, community_id)
    if community is not None:
        community.topic_count = count
        await db.commit()
    return count

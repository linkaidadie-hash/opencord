"""Channel service."""
from __future__ import annotations
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Channel, User
from schemas import ChannelCreate


class ChannelServiceError(Exception):
    pass


async def create_channel(
    db: AsyncSession, creator: User, req: ChannelCreate
) -> Channel:
    existing = await db.execute(
        select(Channel).where(Channel.slug == req.slug)
    )
    if existing.scalar_one_or_none() is not None:
        raise ChannelServiceError(f"Channel slug '{req.slug}' already exists")

    channel = Channel(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        slug=req.slug,
        name=req.name,
        description=req.description,
        visibility=req.visibility,
        created_by=creator.id,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


async def list_channels(
    db: AsyncSession, visibility: str | None = None, limit: int = 50, offset: int = 0
) -> list[Channel]:
    stmt = select(Channel).order_by(Channel.post_count.desc(), Channel.created_at.desc())
    if visibility:
        stmt = stmt.where(Channel.visibility == visibility)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_channel_by_slug(db: AsyncSession, slug: str) -> Channel | None:
    result = await db.execute(select(Channel).where(Channel.slug == slug))
    return result.scalar_one_or_none()


async def get_channel_by_id(db: AsyncSession, channel_id: uuid.UUID) -> Channel | None:
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    return result.scalar_one_or_none()

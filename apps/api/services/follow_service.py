"""Follow service — Open Topic Network.

C 阶段 follow.target_type 支持 community / topic / project / user
- project 仅预留，无 FK
- 其余三个 target 的存在性在 service 入口轻校验
"""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_topic import (
    DEFAULT_TENANT_ID,
    ensure_follow_target_type,
    ensure_tenant_exists,
    resolve_tenant_id,
)
from models import Follow, Community, Topic, User


class FollowServiceError(Exception):
    pass


async def _check_target_exists(db: AsyncSession, target_type: str, target_id: uuid.UUID) -> None:
    """project 不做存在性检查（无 FK）。其它类型要 target 存在。"""
    if target_type == "community":
        result = await db.execute(
            select(Community.id).where(Community.id == target_id)
        )
    elif target_type == "topic":
        result = await db.execute(
            select(Topic.id).where(Topic.id == target_id)
        )
    elif target_type == "user":
        result = await db.execute(
            select(User.id).where(User.id == target_id)
        )
    else:  # project —— 预留
        return
    if result.scalar_one_or_none() is None:
        raise FollowServiceError(f"{target_type} {target_id} not found")


async def follow(
    db: AsyncSession, follower: User, target_type: str, target_id: uuid.UUID
) -> Follow:
    ensure_follow_target_type(target_type)
    if follower.id == target_id and target_type == "user":
        raise FollowServiceError("Cannot follow yourself")
    await _check_target_exists(db, target_type, target_id)

    tenant_id = resolve_tenant_id(follower)
    await ensure_tenant_exists(db, tenant_id)

    f = Follow(
        tenant_id=tenant_id,
        follower_id=follower.id,
        target_type=target_type,
        target_id=target_id,
    )
    db.add(f)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise FollowServiceError("Already following this target")
    await db.refresh(f)
    return f


async def unfollow(
    db: AsyncSession, follower: User, target_type: str, target_id: uuid.UUID
) -> bool:
    ensure_follow_target_type(target_type)
    tenant_id = resolve_tenant_id(follower)
    result = await db.execute(
        select(Follow).where(
            Follow.tenant_id == tenant_id,
            Follow.follower_id == follower.id,
            Follow.target_type == target_type,
            Follow.target_id == target_id,
        )
    )
    f = result.scalar_one_or_none()
    if f is None:
        return False
    await db.delete(f)
    await db.commit()
    return True


async def list_following(
    db: AsyncSession, follower_id: uuid.UUID,
    viewer: User | None = None,
    target_type: str | None = None,
    limit: int = 100, offset: int = 0,
) -> list[Follow]:
    if target_type:
        ensure_follow_target_type(target_type)
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = select(Follow).where(
        Follow.tenant_id == tenant_id,
        Follow.follower_id == follower_id,
    )
    if target_type:
        stmt = stmt.where(Follow.target_type == target_type)
    stmt = stmt.order_by(Follow.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_followers(
    db: AsyncSession, target_type: str, target_id: uuid.UUID,
    viewer: User | None = None,
    limit: int = 100, offset: int = 0,
) -> list[Follow]:
    ensure_follow_target_type(target_type)
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = (
        select(Follow)
        .where(
            Follow.tenant_id == tenant_id,
            Follow.target_type == target_type,
            Follow.target_id == target_id,
        )
        .order_by(Follow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

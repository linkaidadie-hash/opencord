"""Signal service — Open Plaza (C2-lite)."""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_topic import (
    DEFAULT_TENANT_ID,
    ensure_signal_intent_type,
    ensure_signal_visibility,
    ensure_tenant_exists,
    resolve_tenant_id,
)
from models import Signal, Topic, User


class SignalServiceError(Exception):
    pass


async def _validate_topic_if_present(db: AsyncSession, topic_id: uuid.UUID | None) -> None:
    """Signal 可以不绑 topic（广场闲逛时挂的）；绑了就必须存在。"""
    if topic_id is None:
        return
    result = await db.execute(select(Topic.id).where(Topic.id == topic_id))
    if result.scalar_one_or_none() is None:
        raise SignalServiceError(f"Topic {topic_id} not found")


async def create_signal(
    db: AsyncSession, author: User,
    topic_id: uuid.UUID | None,
    intent_type: str,
    title: str,
    body: str | None,
    tags: list[str],
    visibility: str,
    expires_at,
) -> Signal:
    ensure_signal_intent_type(intent_type)
    ensure_signal_visibility(visibility)
    await _validate_topic_if_present(db, topic_id)

    tenant_id = resolve_tenant_id(author)
    await ensure_tenant_exists(db, tenant_id)

    sig = Signal(
        tenant_id=tenant_id,
        user_id=author.id,
        topic_id=topic_id,
        intent_type=intent_type,
        title=title,
        body=body,
        tags=tags or [],
        visibility=visibility,
        expires_at=expires_at,
    )
    db.add(sig)
    await db.commit()
    await db.refresh(sig)
    return sig


async def list_signals(
    db: AsyncSession,
    viewer: User | None = None,
    intent_type: str | None = None,
    topic_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Signal]:
    if intent_type:
        ensure_signal_intent_type(intent_type)
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = select(Signal).where(
        Signal.tenant_id == tenant_id,
        Signal.visibility == "public",  # 广场列表只出 public
    )
    if intent_type:
        stmt = stmt.where(Signal.intent_type == intent_type)
    if topic_id:
        stmt = stmt.where(Signal.topic_id == topic_id)
    stmt = stmt.order_by(Signal.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_signal_by_id(
    db: AsyncSession, signal_id: uuid.UUID, viewer: User | None = None
) -> Signal | None:
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    result = await db.execute(
        select(Signal).where(
            Signal.id == signal_id,
            Signal.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()

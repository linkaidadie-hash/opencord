"""Relation service — Open Topic Network.

通用图边：subject -(relation_type)-> object
- subject_type / object_type / relation_type 在 service 入口由 core/open_topic 校验
- 重复插入由 uq_relations_edge 兜底（应用层也做 check 给友好 400）
- 实际业务校验（target_id 是否存在对应实体）不在 C 阶段做；留 TODO 给后续阶段
"""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.open_topic import (
    DEFAULT_TENANT_ID,
    ensure_subject_type,
    ensure_object_type,
    ensure_relation_type,
    ensure_tenant_exists,
    resolve_tenant_id,
)
from models import Relation


class RelationServiceError(Exception):
    pass


async def create_relation(
    db: AsyncSession,
    creator,  # User | None
    subject_type: str,
    subject_id: uuid.UUID,
    relation_type: str,
    object_type: str,
    object_id: uuid.UUID,
    weight: float = 1.0,
) -> Relation:
    ensure_subject_type(subject_type)
    ensure_object_type(object_type)
    ensure_relation_type(relation_type)

    if subject_id == object_id and subject_type == object_type:
        raise RelationServiceError("Self-loop on same-typed subject/object is not allowed")

    tenant_id = resolve_tenant_id(creator)
    await ensure_tenant_exists(db, tenant_id)

    rel = Relation(
        tenant_id=tenant_id,
        subject_type=subject_type,
        subject_id=subject_id,
        relation_type=relation_type,
        object_type=object_type,
        object_id=object_id,
        weight=weight,
    )
    db.add(rel)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise RelationServiceError("Relation already exists")
    await db.refresh(rel)
    return rel


async def list_relations_out(
    db: AsyncSession,
    subject_type: str,
    subject_id: uuid.UUID,
    viewer=None,
    relation_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Relation]:
    ensure_subject_type(subject_type)
    if relation_type:
        ensure_relation_type(relation_type)
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = select(Relation).where(
        Relation.tenant_id == tenant_id,
        Relation.subject_type == subject_type,
        Relation.subject_id == subject_id,
    )
    if relation_type:
        stmt = stmt.where(Relation.relation_type == relation_type)
    stmt = stmt.order_by(Relation.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_relations_in(
    db: AsyncSession,
    object_type: str,
    object_id: uuid.UUID,
    viewer=None,
    relation_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Relation]:
    ensure_object_type(object_type)
    if relation_type:
        ensure_relation_type(relation_type)
    tenant_id = resolve_tenant_id(viewer) if viewer is not None else uuid.UUID(DEFAULT_TENANT_ID)
    stmt = select(Relation).where(
        Relation.tenant_id == tenant_id,
        Relation.object_type == object_type,
        Relation.object_id == object_id,
    )
    if relation_type:
        stmt = stmt.where(Relation.relation_type == relation_type)
    stmt = stmt.order_by(Relation.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_relation(db: AsyncSession, relation: Relation) -> None:
    await db.delete(relation)
    await db.commit()

"""Open Topic Network — Topics API (C 阶段)."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import TopicCreate, TopicUpdate, TopicPublic, TopicListItem
from core.open_topic import TenantMissingError
from services import topic_service
from services.topic_service import TopicServiceError


router = APIRouter()


@router.get("", response_model=list[TopicListItem])
async def list_topics(
    community_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        topics = await topic_service.list_topics(
            db, viewer=user, community_id=community_id, status=status,
            limit=limit, offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return [TopicListItem.model_validate(t) for t in topics]


@router.post("", response_model=TopicPublic, status_code=201)
async def create_topic(
    req: TopicCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        t = await topic_service.create_topic(
            db, user, req.community_id, req.slug, req.title, req.body_md,
        )
    except TopicServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return TopicPublic.model_validate(t)


@router.get("/{topic_id}", response_model=TopicPublic)
async def get_topic(
    topic_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    t = await topic_service.get_topic_by_id(db, topic_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicPublic.model_validate(t)


@router.patch("/{topic_id}", response_model=TopicPublic)
async def update_topic(
    topic_id: uuid.UUID,
    req: TopicUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    t = await topic_service.get_topic_by_id(db, topic_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    if t.created_by != user.id and user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Not your topic")
    if req.title is not None:
        t.title = req.title
    if req.body_md is not None:
        t.body_md = req.body_md
    if req.status is not None:
        try:
            t = await topic_service.update_topic_status(db, t, req.status)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        await db.commit()
        await db.refresh(t)
    return TopicPublic.model_validate(t)

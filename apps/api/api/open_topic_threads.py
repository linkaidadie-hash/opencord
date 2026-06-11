"""Open Topic Network — Threads API (C 阶段).

注意：thread 不接 comments；thread 自身就是讨论流条目。
"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import ThreadCreate, ThreadPublic
from core.open_topic import TenantMissingError
from services import thread_service
from services.thread_service import ThreadServiceError


router = APIRouter()


@router.get("", response_model=list[ThreadPublic])
async def list_threads(
    topic_id: uuid.UUID = Query(...),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        threads = await thread_service.list_threads_by_topic(
            db, topic_id, viewer=user, limit=limit, offset=offset,
        )
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return [ThreadPublic.model_validate(t) for t in threads]


@router.post("", response_model=ThreadPublic, status_code=201)
async def create_thread(
    req: ThreadCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        t = await thread_service.create_thread(
            db, user, req.topic_id, req.parent_id, req.body_md,
        )
    except ThreadServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return ThreadPublic.model_validate(t)


@router.get("/{thread_id}", response_model=ThreadPublic)
async def get_thread(
    thread_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    t = await thread_service.get_thread_by_id(db, thread_id)
    if t is None or t.status == "deleted":
        raise HTTPException(status_code=404, detail="Thread not found")
    return ThreadPublic.model_validate(t)

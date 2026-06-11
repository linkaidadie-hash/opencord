"""Open Plaza — Signals API (C2-lite)."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import SignalCreate, SignalPublic, SignalListItem
from core.open_topic import TenantMissingError
from services import signal_service
from services.signal_service import SignalServiceError


router = APIRouter()


@router.get("", response_model=list[SignalListItem])
async def list_signals(
    intent_type: str | None = Query(default=None),
    topic_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await signal_service.list_signals(
            db, viewer=user, intent_type=intent_type, topic_id=topic_id,
            limit=limit, offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return [SignalListItem.model_validate(r) for r in rows]


@router.post("", response_model=SignalPublic, status_code=201)
async def create_signal(
    req: SignalCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        sig = await signal_service.create_signal(
            db, author=user,
            topic_id=req.topic_id,
            intent_type=req.intent_type,
            title=req.title,
            body=req.body,
            tags=req.tags or [],
            visibility=req.visibility,
            expires_at=req.expires_at,
        )
    except SignalServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return SignalPublic.model_validate(sig)


@router.get("/{signal_id}", response_model=SignalPublic)
async def get_signal(
    signal_id: uuid.UUID,
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        sig = await signal_service.get_signal_by_id(db, signal_id, viewer=user)
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    if sig is None or sig.visibility == "private":
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalPublic.model_validate(sig)

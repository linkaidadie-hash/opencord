"""Open Topic Network — Follows API (C 阶段)."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import FollowCreate, FollowPublic
from core.open_topic import TenantMissingError
from services import follow_service
from services.follow_service import FollowServiceError


router = APIRouter()


@router.get("/me", response_model=list[FollowPublic])
async def list_my_following(
    target_type: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await follow_service.list_following(
            db, user.id, viewer=user, target_type=target_type,
            limit=limit, offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return [FollowPublic.model_validate(r) for r in rows]


@router.get("/followers", response_model=list[FollowPublic])
async def list_followers_of(
    target_type: str = Query(...),
    target_id: uuid.UUID = Query(...),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        rows = await follow_service.list_followers(
            db, target_type, target_id, viewer=user,
            limit=limit, offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return [FollowPublic.model_validate(r) for r in rows]


@router.post("", response_model=FollowPublic, status_code=201)
async def follow_target(
    req: FollowCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        f = await follow_service.follow(db, user, req.target_type, req.target_id)
    except FollowServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return FollowPublic.model_validate(f)


@router.delete("", status_code=204)
async def unfollow_target(
    target_type: str = Query(...),
    target_id: uuid.UUID = Query(...),
    user: CurrentUser = ...,
    db: AsyncSession = Depends(get_db),
):
    try:
        ok = await follow_service.unfollow(db, user, target_type, target_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    if not ok:
        raise HTTPException(status_code=404, detail="Not following this target")
    return None

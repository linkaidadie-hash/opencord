"""Open Topic Network — Communities API (C 阶段)."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import CommunityCreate, CommunityPublic
from core.open_topic import TenantMissingError
from services import community_service
from services.community_service import CommunityServiceError


router = APIRouter()


@router.get("", response_model=list[CommunityPublic])
async def list_communities(
    visibility: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = ...,  # 仍需登录；只读路径也走 viewer 解析
    db: AsyncSession = Depends(get_db),
):
    try:
        comms = await community_service.list_communities(
            db, viewer=user, visibility=visibility, limit=limit, offset=offset,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return [CommunityPublic.model_validate(c) for c in comms]


@router.post("", response_model=CommunityPublic, status_code=201)
async def create_community(
    req: CommunityCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        c = await community_service.create_community(
            db, user, req.slug, req.name, req.description, req.visibility,
        )
    except CommunityServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return CommunityPublic.model_validate(c)


@router.get("/{community_id}", response_model=CommunityPublic)
async def get_community(
    community_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    c = await community_service.get_community_by_id(db, community_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Community not found")
    return CommunityPublic.model_validate(c)

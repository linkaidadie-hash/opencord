"""/api/channels/*"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import ChannelCreate, ChannelPublic
from services import channel_service
from services.channel_service import ChannelServiceError


router = APIRouter()


@router.get("", response_model=list[ChannelPublic])
async def list_channels(
    visibility: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    channels = await channel_service.list_channels(db, visibility, limit, offset)
    return [ChannelPublic.model_validate(c) for c in channels]


@router.post("", response_model=ChannelPublic, status_code=201)
async def create_channel(
    req: ChannelCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        ch = await channel_service.create_channel(db, user, req)
    except ChannelServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ChannelPublic.model_validate(ch)


@router.get("/{slug}", response_model=ChannelPublic)
async def get_channel(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    ch = await channel_service.get_channel_by_slug(db, slug)
    if ch is None:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ChannelPublic.model_validate(ch)

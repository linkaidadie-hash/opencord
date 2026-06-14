"""Open Plaza — Plaza aggregate API (C2-lite)."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth import OptionalUser
from database import get_db
from schemas import PlazaResponse
from core.open_topic import TenantMissingError
from services import plaza_service


router = APIRouter()


@router.get("", response_model=PlazaResponse)
async def get_plaza(
    user: OptionalUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await plaza_service.get_plaza(db, viewer=user)
    except TenantMissingError as e:
        raise HTTPException(status_code=503, detail=f"Default tenant is missing: {e}")
    return PlazaResponse(
        description=data["description"],
        recent_topics=[t for t in data["recent_topics"]],
        recent_signals=[s for s in data["recent_signals"]],
        hot=data["hot"],
    )

"""/api/notifications/* — 通知列表 + 标记已读"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import NotificationPublic, UserPublic
from services import notification_service


router = APIRouter()


@router.get("", response_model=list[NotificationPublic])
async def list_notifications(
    user: CurrentUser,
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    notifs = await notification_service.list_for_user(db, user.id, unread_only, limit)
    out = []
    for n in notifs:
        out.append(NotificationPublic(
            id=n.id,
            type=n.type,
            actor=UserPublic.model_validate(n.actor) if n.actor else None,
            target_type=n.target_type,
            target_id=n.target_id,
            payload=n.payload,
            read_at=n.read_at,
            created_at=n.created_at,
        ))
    return out


class MarkReadRequest(BaseModel):
    notification_ids: list[uuid.UUID] | None = None  # None 表示全部


@router.post("/mark-read")
async def mark_read(
    req: MarkReadRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    count = await notification_service.mark_read(db, user.id, req.notification_ids)
    return {"marked_read": count}

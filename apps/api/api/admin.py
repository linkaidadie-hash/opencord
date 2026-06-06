"""/api/admin/* — 管理员操作"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentAdmin
from database import get_db
from models import User, Post
from schemas import AdminUserAction, UserPublic
from services import user_service
from services.user_service import UserServiceError
from services.post_service import delete_post as svc_delete_post


router = APIRouter()


@router.post("/users/{user_id}/action", response_model=UserPublic)
async def user_action(
    user_id: uuid.UUID,
    req: AdminUserAction,
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id and req.action in ("ban", "suspend", "demote"):
        raise HTTPException(status_code=400, detail="Cannot perform this action on yourself")
    try:
        await user_service.admin_action(db, admin, target, req.action, req.reason)
    except UserServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UserPublic.model_validate(target)


@router.delete("/posts/{post_id}", status_code=204)
async def admin_delete_post(
    post_id: uuid.UUID,
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    await svc_delete_post(db, post)
    return None

"""/api/posts/{post_id}/comments + /api/comments/*"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import CommentCreate, CommentPublic, UserPublic
from services import comment_service
from services.comment_service import CommentServiceError


router = APIRouter()


def _to_public(c) -> CommentPublic:
    return CommentPublic(
        id=c.id,
        post_id=c.post_id,
        parent_id=c.parent_id,
        author=UserPublic.model_validate(c.author) if c.author else None,
        body_md=c.body_md,
        body_html=c.body_html,
        created_at=c.created_at,
    )


@router.get("/by-post/{post_id}", response_model=list[CommentPublic])
async def list_comments(
    post_id: uuid.UUID,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    comments = await comment_service.list_comments(db, post_id, limit, offset)
    return [_to_public(c) for c in comments]


@router.post("", response_model=CommentPublic, status_code=201)
async def create_comment(
    req: CommentCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        c = await comment_service.create_comment(db, user, req)
    except CommentServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_public(c)

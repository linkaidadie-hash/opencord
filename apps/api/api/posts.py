"""/api/posts/* — 帖子 CRUD + 列表"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import CurrentUser, get_current_user
from database import get_db
from models import Post, User
from schemas import PostCreate, PostUpdate, PostPublic, PostListItem, UserPublic
from services import post_service
from services.post_service import PostServiceError, get_post_tags


router = APIRouter()


def _to_public(post: Post, tag_slugs: list[str]) -> PostPublic:
    author = UserPublic.model_validate(post.author) if post.author else None
    return PostPublic(
        id=post.id,
        channel_id=post.channel_id,
        author=author,
        title=post.title,
        body_md=post.body_md,
        body_html=post.body_html,
        status=post.status,
        pinned=post.pinned,
        view_count=post.view_count,
        comment_count=post.comment_count,
        ai_summary=post.ai_summary,
        ai_summary_at=post.ai_summary_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        tag_slugs=tag_slugs,
    )


def _to_list_item(post: Post, tag_slugs: list[str]) -> PostListItem:
    author = UserPublic.model_validate(post.author) if post.author else None
    return PostListItem(
        id=post.id,
        channel_id=post.channel_id,
        author=author,
        title=post.title,
        status=post.status,
        pinned=post.pinned,
        comment_count=post.comment_count,
        ai_summary=post.ai_summary,
        created_at=post.created_at,
        tag_slugs=tag_slugs,
    )


@router.get("", response_model=list[PostListItem])
async def list_posts(
    channel_id: uuid.UUID | None = Query(default=None),
    author_id: uuid.UUID | None = Query(default=None),
    tag: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    posts = await post_service.list_posts(db, channel_id, author_id, tag, limit, offset)
    items = []
    for p in posts:
        tags = await get_post_tags(db, p.id)
        items.append(_to_list_item(p, tags))
    return items


@router.post("", response_model=PostPublic, status_code=201)
async def create_post(
    req: PostCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    try:
        post = await post_service.create_post(db, user, req)
    except PostServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    tags = await get_post_tags(db, post.id)
    return _to_public(post, tags)


@router.get("/{post_id}", response_model=PostPublic)
async def get_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    post = await post_service.get_post_by_id(db, post_id, increment_view=True)
    if post is None or post.status == "deleted":
        raise HTTPException(status_code=404, detail="Post not found")
    tags = await get_post_tags(db, post.id)
    return _to_public(post, tags)


@router.patch("/{post_id}", response_model=PostPublic)
async def update_post(
    post_id: uuid.UUID,
    req: PostUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    post = await post_service.get_post_by_id(db, post_id, increment_view=False)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id and user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Not your post")
    post = await post_service.update_post(db, post, req)
    tags = await get_post_tags(db, post.id)
    return _to_public(post, tags)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: uuid.UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    post = await post_service.get_post_by_id(db, post_id, increment_view=False)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id and user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Not your post")
    await post_service.delete_post(db, post)
    return None

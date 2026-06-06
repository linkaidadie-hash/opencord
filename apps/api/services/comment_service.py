"""Comment service."""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Comment, Post, User, Notification
from schemas import CommentCreate
from services.markdown import render_markdown, safe_html


class CommentServiceError(Exception):
    pass


async def create_comment(db: AsyncSession, author: User, req: CommentCreate) -> Comment:
    post = await db.get(Post, req.post_id)
    if post is None or post.status != "published":
        raise CommentServiceError(f"Post not found: {req.post_id}")

    if req.parent_id:
        parent = await db.get(Comment, req.parent_id)
        if parent is None or parent.post_id != req.post_id:
            raise CommentServiceError("Invalid parent comment")

    html = safe_html(render_markdown(req.body_md))
    comment = Comment(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        post_id=post.id,
        author_id=author.id,
        parent_id=req.parent_id,
        body_md=req.body_md,
        body_html=html,
    )
    db.add(comment)
    post.comment_count += 1

    # 通知帖子作者（如果不是自己评论）
    if post.author_id != author.id:
        notif = Notification(
            tenant_id=post.tenant_id,
            user_id=post.author_id,
            type="post.commented",
            actor_id=author.id,
            target_type="post",
            target_id=post.id,
            payload={"comment_id": str(comment.id), "excerpt": req.body_md[:120]},
        )
        db.add(notif)

    await db.commit()
    return await get_comment_by_id(db, comment.id)


async def get_comment_by_id(db: AsyncSession, comment_id: uuid.UUID) -> Comment | None:
    result = await db.execute(
        select(Comment).options(selectinload(Comment.author)).where(Comment.id == comment_id)
    )
    return result.scalar_one_or_none()


async def list_comments(
    db: AsyncSession, post_id: uuid.UUID, limit: int = 100, offset: int = 0
) -> list[Comment]:
    stmt = (
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.post_id == post_id, Comment.status == "published")
        .order_by(Comment.created_at)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

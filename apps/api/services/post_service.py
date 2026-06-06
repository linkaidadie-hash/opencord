"""Post service: create, list, get, update, delete."""
from __future__ import annotations
import uuid
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Post, Channel, User, Tag, PostTag
from schemas import PostCreate, PostUpdate
from services.markdown import render_markdown, safe_html


class PostServiceError(Exception):
    pass


async def create_post(db: AsyncSession, author: User, req: PostCreate) -> Post:
    channel = await db.get(Channel, req.channel_id)
    if channel is None:
        raise PostServiceError(f"Channel not found: {req.channel_id}")

    html = safe_html(render_markdown(req.body_md))
    post = Post(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        channel_id=channel.id,
        author_id=author.id,
        title=req.title,
        body_md=req.body_md,
        body_html=html,
        status="published",
    )
    db.add(post)
    await db.flush()

    # 标签
    for tag_slug in req.tag_slugs:
        tag = await _get_or_create_tag(db, tag_slug)
        db.add(PostTag(post_id=post.id, tag_id=tag.id, tenant_id=post.tenant_id))
        tag.post_count += 1

    channel.post_count += 1
    await db.commit()

    # reload with relationships
    return await get_post_by_id(db, post.id, increment_view=False)


async def get_post_by_id(
    db: AsyncSession, post_id: uuid.UUID, increment_view: bool = True
) -> Post | None:
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.id == post_id)
    )
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post is not None and increment_view:
        post.view_count += 1
        await db.commit()
    return post


async def list_posts(
    db: AsyncSession,
    channel_id: uuid.UUID | None = None,
    author_id: uuid.UUID | None = None,
    tag_slug: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Post]:
    stmt = (
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.status == "published")
        .order_by(Post.pinned.desc(), Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if channel_id:
        stmt = stmt.where(Post.channel_id == channel_id)
    if author_id:
        stmt = stmt.where(Post.author_id == author_id)
    if tag_slug:
        stmt = stmt.join(PostTag, PostTag.post_id == Post.id).join(
            Tag, Tag.id == PostTag.tag_id
        ).where(Tag.slug == tag_slug)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_post(
    db: AsyncSession, post: Post, req: PostUpdate
) -> Post:
    if req.title is not None:
        post.title = req.title
    if req.body_md is not None:
        post.body_md = req.body_md
        post.body_html = safe_html(render_markdown(req.body_md))
    await db.commit()
    await db.refresh(post)
    return post


async def delete_post(db: AsyncSession, post: Post) -> None:
    channel = await db.get(Channel, post.channel_id)
    post.status = "deleted"
    if channel and channel.post_count > 0:
        channel.post_count -= 1
    await db.commit()


async def _get_or_create_tag(db: AsyncSession, slug: str) -> Tag:
    result = await db.execute(select(Tag).where(Tag.slug == slug))
    tag = result.scalar_one_or_none()
    if tag:
        return tag
    tag = Tag(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name=slug,
        slug=slug,
    )
    db.add(tag)
    await db.flush()
    return tag


async def get_post_tags(db: AsyncSession, post_id: uuid.UUID) -> list[str]:
    result = await db.execute(
        select(Tag.slug).join(PostTag, PostTag.tag_id == Tag.id).where(PostTag.post_id == post_id)
    )
    return [row[0] for row in result.all()]

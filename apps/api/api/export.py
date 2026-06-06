"""/api/export/* — 用户数据导出（JSON）"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import CurrentUser
from database import get_db
from models import Post, Comment, Notification, APIToken, Channel, Tag, PostTag


router = APIRouter()


@router.get("/me")
async def export_my_data(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """导出当前用户所有数据为 JSON。"""
    posts_result = await db.execute(
        select(Post).where(Post.author_id == user.id).order_by(Post.created_at.desc())
    )
    posts = list(posts_result.scalars().all())

    comments_result = await db.execute(
        select(Comment).where(Comment.author_id == user.id).order_by(Comment.created_at.desc())
    )
    comments = list(comments_result.scalars().all())

    tokens_result = await db.execute(
        select(APIToken).where(APIToken.user_id == user.id)
    )
    tokens = list(tokens_result.scalars().all())

    notifs_result = await db.execute(
        select(Notification).where(Notification.user_id == user.id)
    )
    notifs = list(notifs_result.scalars().all())

    data = {
        "export_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
        },
        "posts": [
            {
                "id": str(p.id),
                "channel_id": str(p.channel_id),
                "title": p.title,
                "body_md": p.body_md,
                "body_html": p.body_html,
                "status": p.status,
                "view_count": p.view_count,
                "comment_count": p.comment_count,
                "ai_summary": p.ai_summary,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in posts
        ],
        "comments": [
            {
                "id": str(c.id),
                "post_id": str(c.post_id),
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "body_md": c.body_md,
                "body_html": c.body_html,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ],
        "api_tokens": [
            {
                "id": str(t.id),
                "name": t.name,
                "token_prefix": t.token_prefix,
                "scopes": t.scopes,
                "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                "created_at": t.created_at.isoformat(),
                "revoked_at": t.revoked_at.isoformat() if t.revoked_at else None,
            }
            for t in tokens
        ],
        "notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "target_type": n.target_type,
                "target_id": str(n.target_id),
                "payload": n.payload,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ],
    }

    # 流式响应
    def _iter():
        yield json.dumps(data, ensure_ascii=False, indent=2, default=str)

    filename = f"opencord-export-{user.username}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
    return StreamingResponse(
        _iter(),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

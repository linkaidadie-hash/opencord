"""AI Summary service: 总结帖子，存缓存。"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from models import Post, AIUsageLog
from services.ai_service import resolve_provider, AIServiceError
from packages.ai import SummarizeOptions


class SummaryServiceError(Exception):
    pass


async def summarize_post(
    db: AsyncSession,
    post: Post,
    *,
    force_refresh: bool = False,
    max_length: int = 300,
    language: str = "zh",
    style: str = "concise",
) -> str:
    """
    总结帖子内容，返回 summary 文本。
    如果 post.ai_summary 已存在且未过期，直接返回缓存。
    """
    if not force_refresh and post.ai_summary:
        return post.ai_summary

    provider = await resolve_provider(db, task="summarize")
    if provider is None:
        raise SummaryServiceError(
            "No AI provider available. Configure one in admin panel."
        )

    options = SummarizeOptions(
        max_length=max_length,
        language=language,
        style=style,
    )

    t0 = datetime.now(timezone.utc)
    try:
        result = await provider.summarize(post.body_md, options)
    except Exception as e:
        # 记录失败
        log = AIUsageLog(
            tenant_id=post.tenant_id,
            provider_id=uuid.UUID(provider.provider_id) if provider.provider_id else None,
            user_id=None,
            task_type="summarize",
            latency_ms=int((datetime.now(timezone.utc) - t0).total_seconds() * 1000),
            error_code=type(e).__name__[:64],
        )
        db.add(log)
        await db.commit()
        raise SummaryServiceError(f"AI summary failed: {e}") from e

    # 写缓存
    post.ai_summary = result.summary
    post.ai_summary_at = datetime.now(timezone.utc)
    post.ai_provider_used = provider.provider_type

    log = AIUsageLog(
        tenant_id=post.tenant_id,
        provider_id=uuid.UUID(provider.provider_id) if provider.provider_id else None,
        user_id=None,
        task_type="summarize",
        tokens_in=result.tokens_in,
        tokens_out=result.tokens_out,
        latency_ms=result.latency_ms,
    )
    db.add(log)

    await db.commit()
    return result.summary

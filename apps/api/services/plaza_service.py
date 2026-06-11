"""Plaza service — Open Plaza 聚合（C2-lite）.

C2-lite 只做"广场首页"：返回最近 topics + 最近 signals。
不做推荐（hot 留空）、不做 encounter、不做匹配。
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

from services import signal_service, topic_service


PLAZA_DESCRIPTION = (
    "A public square for topics, signals, and open encounters. "
    "Hang out, watch what others care about, post a signal — "
    "\"I'm looking for X / I'd love to talk about Y / I can help with Z\"."
)


async def get_plaza(
    db: AsyncSession, viewer=None, recent_limit: int = 10
) -> dict:
    """拼装 Plaza 首页数据。"""
    topics = await topic_service.list_topics(
        db, viewer=viewer, limit=recent_limit, offset=0,
    )
    signals = await signal_service.list_signals(
        db, viewer=viewer, limit=recent_limit, offset=0,
    )
    return {
        "description": PLAZA_DESCRIPTION,
        "recent_topics": topics,
        "recent_signals": signals,
        "hot": [],  # 预留
    }

"""/api/open-topic/* — Open Topic Network 入口聚合（C 阶段 + C2-lite）.

包含子路由：
- /communities
- /topics
- /threads
- /relations
- /follows
- /signals        (C2-lite: Open Plaza)
"""
from fastapi import APIRouter

from api import (
    open_topic_communities,
    open_topic_topics,
    open_topic_threads,
    open_topic_relations,
    open_topic_follows,
    open_topic_signals,
)


router = APIRouter()

router.include_router(open_topic_communities.router, prefix="/communities", tags=["open-topic-communities"])
router.include_router(open_topic_topics.router, prefix="/topics", tags=["open-topic-topics"])
router.include_router(open_topic_threads.router, prefix="/threads", tags=["open-topic-threads"])
router.include_router(open_topic_relations.router, prefix="/relations", tags=["open-topic-relations"])
router.include_router(open_topic_follows.router, prefix="/follows", tags=["open-topic-follows"])
router.include_router(open_topic_signals.router, prefix="/signals", tags=["open-topic-signals"])

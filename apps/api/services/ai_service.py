"""AI Service: 解析 DB 配置，构建 AIProvider 实例，限流。"""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import AIProviderConfig
from packages.ai import AIProviderFactory, AIProvider, get_rate_limiter


class AIServiceError(Exception):
    pass


async def list_providers(db: AsyncSession) -> list[AIProviderConfig]:
    result = await db.execute(
        select(AIProviderConfig).order_by(AIProviderConfig.is_default.desc(), AIProviderConfig.created_at)
    )
    return list(result.scalars().all())


async def get_default_provider(db: AsyncSession) -> AIProviderConfig | None:
    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.is_default == True,
            AIProviderConfig.is_active == True,
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def get_provider_by_id(db: AsyncSession, provider_id: uuid.UUID) -> AIProviderConfig | None:
    return await db.get(AIProviderConfig, provider_id)


def build_provider_instance(config: AIProviderConfig) -> AIProvider:
    """从 DB 配置创建 AIProvider 实例。"""
    return AIProviderFactory.create(
        provider_type=config.provider_type,
        name=config.name,
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
        provider_id=str(config.id),
        rpm_limit=config.rpm_limit,
    )


async def resolve_provider(db: AsyncSession, task: str = "summarize") -> AIProvider | None:
    """
    选一个能用的 provider：
    1. is_default=True
    2. 支持当前 task (chat / summarize / embed)
    3. 通过限流检查
    """
    config = await get_default_provider(db)
    if config is None:
        return None
    if task == "summarize" and not config.supports_summarize:
        return None
    if task == "embed" and not config.supports_embed:
        return None
    if task == "chat" and not config.supports_chat:
        return None
    # 限流
    limiter = get_rate_limiter()
    if not limiter.check(str(config.id), config.rpm_limit):
        # 限流了，尝试找非默认的
        all_configs = await list_providers(db)
        for c in all_configs:
            if c.id == config.id or not c.is_active:
                continue
            if task == "summarize" and not c.supports_summarize:
                continue
            if limiter.check(str(c.id), c.rpm_limit):
                return build_provider_instance(c)
        return None
    return build_provider_instance(config)

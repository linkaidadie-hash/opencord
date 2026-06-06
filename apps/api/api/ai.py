"""/api/ai/* — AI 能力入口（v0.1：summarize + provider 管理）"""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentAdmin
from database import get_db
from models import Post
from schemas import AIProviderCreate, AIProviderPublic
from services import ai_service, ai_summary_service
from services.ai_summary_service import SummaryServiceError


router = APIRouter()


# ---- Provider 管理（admin）----

@router.get("/providers", response_model=list[AIProviderPublic])
async def list_providers(
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
):
    configs = await ai_service.list_providers(db)
    return [AIProviderPublic.model_validate(c) for c in configs]


@router.post("/providers", response_model=AIProviderPublic, status_code=201)
async def create_provider(
    req: AIProviderCreate,
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
):
    from models import AIProviderConfig
    # 如果设为 default，先把别的 default 关掉
    if req.is_default:
        existing = await ai_service.list_providers(db)
        for c in existing:
            c.is_default = False

    config = AIProviderConfig(
        tenant_id=admin.tenant_id,
        name=req.name,
        provider_type=req.provider_type,
        api_key=req.api_key,
        base_url=req.base_url,
        model=req.model,
        is_active=True,
        is_default=req.is_default,
        rpm_limit=req.rpm_limit,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return AIProviderPublic.model_validate(config)


@router.post("/providers/{provider_id}/set-default", response_model=AIProviderPublic)
async def set_default(
    provider_id: uuid.UUID,
    admin: CurrentAdmin,
    db: AsyncSession = Depends(get_db),
):
    config = await ai_service.get_provider_by_id(db, provider_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    # 取消其他 default
    others = await ai_service.list_providers(db)
    for c in others:
        c.is_default = (c.id == config.id)
    config.is_active = True
    await db.commit()
    await db.refresh(config)
    return AIProviderPublic.model_validate(config)


# ---- 总结（user 可调）----

@router.post("/summarize-post/{post_id}")
async def summarize_post(
    post_id: uuid.UUID,
    user: CurrentAdmin,  # v0.1 只允许 admin 触发；v0.2 加 "admin 配置后，任何人可看"
    force_refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if post is None or post.status != "published":
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        summary = await ai_summary_service.summarize_post(db, post, force_refresh=force_refresh)
    except SummaryServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"post_id": str(post.id), "ai_summary": summary}

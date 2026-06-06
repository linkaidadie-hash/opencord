"""/api/users/me/tokens — 用户级 API Token 管理（v0.1 限定用户级，v0.2 加 Bot 级别）"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser, generate_api_token, hash_api_token
from database import get_db
from models import APIToken
from schemas import APITokenCreate, APITokenCreated, APITokenPublic


router = APIRouter()


@router.get("/me/tokens", response_model=list[APITokenPublic])
async def list_my_tokens(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIToken)
        .where(APIToken.user_id == user.id)
        .order_by(APIToken.created_at.desc())
    )
    return [APITokenPublic.model_validate(t) for t in result.scalars().all()]


@router.post("/me/tokens", response_model=APITokenCreated, status_code=201)
async def create_token(
    req: APITokenCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    raw, h, prefix = generate_api_token()
    expires_at = None
    if req.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days)

    token = APIToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=req.name,
        token_hash=h,
        token_prefix=prefix,
        scopes=req.scopes,
        expires_at=expires_at,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return APITokenCreated(
        id=token.id,
        name=token.name,
        token=raw,  # 明文只此一次返回
        token_prefix=token.token_prefix,
        scopes=token.scopes,
        expires_at=token.expires_at,
        created_at=token.created_at,
    )


@router.delete("/me/tokens/{token_id}", status_code=204)
async def revoke_token(
    token_id: uuid.UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIToken).where(APIToken.id == token_id, APIToken.user_id == user.id)
    )
    token = result.scalar_one_or_none()
    if token is None:
        raise HTTPException(status_code=404, detail="Token not found")
    if token.revoked_at is None:
        token.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    return None

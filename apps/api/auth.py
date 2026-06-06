"""OpenCord Auth: JWT + API Token."""
from __future__ import annotations
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import User, APIToken


# =====================================================
# Password hashing
# =====================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# =====================================================
# JWT
# =====================================================
bearer_scheme = HTTPBearer(auto_error=False)


def create_jwt(user_id: str) -> tuple[str, int]:
    """返回 (token, expires_in_seconds)"""
    expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "jwt",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def decode_jwt(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


# =====================================================
# API Token
# =====================================================
def generate_api_token() -> tuple[str, str, str]:
    """返回 (raw_token, token_hash, token_prefix)"""
    raw = f"oc_{secrets.token_urlsafe(32)}"
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, h, raw[:8]


def hash_api_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# =====================================================
# Current user dependencies
# =====================================================
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id_str: str | None = None

    # Try API Token first (raw token starts with "oc_")
    if token.startswith("oc_"):
        token_hash = hash_api_token(token)
        result = await db.execute(
            select(APIToken).where(
                APIToken.token_hash == token_hash,
                APIToken.revoked_at.is_(None),
            )
        )
        api_token = result.scalar_one_or_none()
        if api_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API token",
            )
        if api_token.expires_at and api_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API token expired",
            )
        # Update last_used_at
        api_token.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        user_id_str = str(api_token.user_id)
    else:
        # JWT
        user_id_str = decode_jwt(token)

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    result = await db.execute(select(User).where(User.id == user_id_str))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.status == "banned":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is banned",
        )
    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is suspended",
        )
    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if user.role not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]

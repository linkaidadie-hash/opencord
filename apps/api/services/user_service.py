"""User service: registration, login, profile, admin actions."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth import hash_password, verify_password, create_jwt
from models import User
from schemas import RegisterRequest, UserUpdate


class UserServiceError(Exception):
    pass


async def register_user(db: AsyncSession, req: RegisterRequest) -> tuple[User, str, int]:
    """注册。返回 (user, jwt_token, expires_in_seconds)"""
    # 检查 email / username 唯一
    existing = await db.execute(
        select(User).where(
            (User.email == req.email.lower()) | (User.username == req.username)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise UserServiceError("Email or username already taken")

    user = User(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email=req.email.lower(),
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name or req.username,
        role="member",
        status="active",
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise UserServiceError(f"Registration failed: {e.orig}")
    await db.refresh(user)

    token, expires_in = create_jwt(str(user.id))
    return user, token, expires_in


async def login_user(db: AsyncSession, email_or_username: str, password: str) -> tuple[User, str, int]:
    """登录。"""
    result = await db.execute(
        select(User).where(
            (User.email == email_or_username.lower()) | (User.username == email_or_username)
        )
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise UserServiceError("Invalid credentials")
    if user.status != "active":
        raise UserServiceError(f"Account is {user.status}")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    token, expires_in = create_jwt(str(user.id))
    return user, token, expires_in


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user: User, updates: UserUpdate) -> User:
    if updates.display_name is not None:
        user.display_name = updates.display_name
    if updates.bio is not None:
        user.bio = updates.bio
    if updates.avatar_url is not None:
        user.avatar_url = updates.avatar_url
    await db.commit()
    await db.refresh(user)
    return user


async def admin_action(
    db: AsyncSession,
    actor: User,
    target: User,
    action: str,
    reason: str | None,
) -> None:
    """封号 / 解封 / 暂停 / 升降级"""
    if action == "ban":
        target.status = "banned"
    elif action == "unban":
        target.status = "active"
    elif action == "suspend":
        target.status = "suspended"
    elif action == "promote":
        target.role = "admin" if actor.role == "admin" else "moderator"
    elif action == "demote":
        target.role = "member"
    else:
        raise UserServiceError(f"Unknown action: {action}")

    # Audit log (skip in v0.1 to avoid extra model load)
    await db.commit()
    await db.refresh(target)

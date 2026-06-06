"""/api/users/* — 公开用户主页 + 自己更新资料"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from database import get_db
from schemas import UserPublic, UserUpdate
from services import user_service


router = APIRouter()


@router.get("/{username}", response_model=UserPublic)
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    req: UserUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.update_user(db, user, req)
    return UserPublic.model_validate(user)

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, City, School
from app.schema.api import UpdateMeRequest
from app.service.platform import (
    build_achievements,
    get_user_stats,
    paginate_list,
    serialize_city,
    serialize_school,
    serialize_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stats = await get_user_stats(db, user)
    city = None
    school = None
    if user.city_id:
        city = (await db.execute(select(City).where(City.id == user.city_id))).scalar_one_or_none()
    if user.school_id:
        school = (await db.execute(select(School).where(School.id == user.school_id))).scalar_one_or_none()

    return {
        **serialize_user(user),
        "city": serialize_city(city) if city else None,
        "school": serialize_school(school) if school else None,
        "stats": stats,
    }


@router.patch("/me")
async def update_me(payload: UpdateMeRequest, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.avatarUrl is not None:
        user.avatar_url = payload.avatarUrl.strip() if payload.avatarUrl else None
    if payload.grade is not None:
        user.grade = payload.grade

    await db.commit()
    await db.refresh(user)
    return serialize_user(user)


@router.get("/me/stats")
async def get_my_stats(user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_user_stats(db, user)


@router.get("/me/achievements")
async def get_my_achievements(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_user_stats(db, user)
    unlocked = build_achievements(stats, user)
    page, next_cursor = paginate_list(unlocked, cursor, limit)
    return {
        "data": page,
        "nextCursor": next_cursor,
    }

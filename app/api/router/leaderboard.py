from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, City, School

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/")
async def get_leaderboard(
    scope: str = Query(default="class"),
    limit: int = Query(default=50, ge=1, le=200),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scope = scope if scope in {"class", "school", "city"} else "class"

    query = select(AppUser)
    if scope == "class":
        query = query.where(AppUser.grade == user.grade, AppUser.school_id == user.school_id)
    elif scope == "school":
        query = query.where(AppUser.school_id == user.school_id)
    elif scope == "city":
        query = query.where(AppUser.city_id == user.city_id)

    rows = (
        (
            await db.execute(
                query.order_by(
                    AppUser.xp_total.desc(),
                    AppUser.updated_at.asc(),
                    AppUser.id.asc(),
                )
            )
        )
        .scalars()
        .all()
    )

    school_ids = {item.school_id for item in rows if item.school_id}
    city_ids = {item.city_id for item in rows if item.city_id}

    schools = {}
    cities = {}
    if school_ids:
        school_rows = (await db.execute(select(School).where(School.id.in_(school_ids)))).scalars().all()
        schools = {school.id: school for school in school_rows}
    if city_ids:
        city_rows = (await db.execute(select(City).where(City.id.in_(city_ids)))).scalars().all()
        cities = {city.id: city for city in city_rows}

    entries = []
    for idx, item in enumerate(rows, start=1):
        school = schools.get(item.school_id) if item.school_id else None
        city = cities.get(item.city_id) if item.city_id else None
        entries.append(
            {
                "rank": idx,
                "xp": item.xp_total,
                "user": {
                    "id": item.id,
                    "name": item.name,
                    "avatarUrl": item.avatar_url,
                    "grade": item.grade,
                    "xpTotal": item.xp_total,
                    "school": {"id": school.id, "name": school.name} if school else None,
                    "city": {"id": city.id, "name": city.name} if city else None,
                },
            }
        )

    current_user_entry = next((entry for entry in entries if entry["user"]["id"] == user.id), None)
    return {
        "scope": scope,
        "leaderboard": entries[:limit],
        "currentUser": current_user_entry,
    }

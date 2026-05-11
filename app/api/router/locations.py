from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.db.models.education import City, School
from app.service.platform import paginate_list, serialize_city, serialize_school

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/cities")
async def get_cities(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    cities = (await db.execute(select(City).order_by(City.name.asc()))).scalars().all()
    items = [serialize_city(city) for city in cities]
    page, next_cursor = paginate_list(items, cursor, limit)
    return {"data": page, "nextCursor": next_cursor}


@router.get("/cities/{city_id}/schools")
async def get_schools_by_city(
    city_id: str,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    schools = (
        (await db.execute(select(School).where(School.city_id == city_id).order_by(School.name.asc())))
        .scalars()
        .all()
    )
    items = [serialize_school(school) for school in schools]
    page, next_cursor = paginate_list(items, cursor, limit)
    return {"data": page, "nextCursor": next_cursor}

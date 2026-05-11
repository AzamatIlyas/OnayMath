from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, Topic
from app.service.platform import build_topic_summary, paginate_list

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/")
async def get_topics(
    grade: int | None = Query(default=None, ge=1, le=11),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_grade = grade if grade is not None else user.grade
    topics = (
        (
            await db.execute(
                select(Topic)
                .where(Topic.grade == target_grade, Topic.is_published.is_(True))
                .order_by(Topic.order_index.asc(), Topic.id.asc())
            )
        )
        .scalars()
        .all()
    )

    summary = []
    for topic in topics:
        item = await build_topic_summary(db, topic, user.id)
        summary.append({k: v for k, v in item.items() if k != "lessons"})

    page, next_cursor = paginate_list(summary, cursor, limit)
    return {"data": page, "nextCursor": next_cursor}


@router.get("/{topic_id}")
async def get_topic(topic_id: str, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    topic = (await db.execute(select(Topic).where(Topic.id == topic_id, Topic.is_published.is_(True)))).scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail={"error": "Topic not found", "code": "TOPIC_NOT_FOUND"})

    return await build_topic_summary(db, topic, user.id)

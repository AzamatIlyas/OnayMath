from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, Lesson
from app.service.platform import get_or_create_progress, serialize_progress

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{lesson_id}")
async def get_lesson(lesson_id: str, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"error": "Lesson not found", "code": "LESSON_NOT_FOUND"})

    progress = await get_or_create_progress(db, user.id, lesson.id)
    await db.commit()

    return {
        "id": lesson.id,
        "topicId": lesson.topic_id,
        "title": lesson.title,
        "content": lesson.content,
        "order": lesson.order_index,
        "durationMinutes": lesson.duration_minutes,
        "progress": serialize_progress(progress),
    }


@router.post("/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"error": "Lesson not found", "code": "LESSON_NOT_FOUND"})

    progress = await get_or_create_progress(db, user.id, lesson.id)
    if progress.status == "NOT_STARTED":
        progress.status = "IN_PROGRESS"
    await db.commit()

    return {"success": True, "xpEarned": 0}

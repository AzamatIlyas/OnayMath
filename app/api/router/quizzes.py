from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, Lesson, QuizQuestion
from app.schema.api import QuizSubmitRequest
from app.service.platform import get_or_create_progress, update_streak

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/{lesson_id}/questions")
async def get_questions(lesson_id: str, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"error": "Lesson not found", "code": "LESSON_NOT_FOUND"})

    questions = (
        (
            await db.execute(
                select(QuizQuestion).where(QuizQuestion.lesson_id == lesson_id).order_by(QuizQuestion.id.asc()).limit(5)
            )
        )
        .scalars()
        .all()
    )
    return {
        "lessonId": lesson_id,
        "questions": [{"id": q.id, "text": q.text, "options": q.options} for q in questions],
    }


@router.post("/{lesson_id}/submit")
async def submit_quiz(
    lesson_id: str,
    payload: QuizSubmitRequest,
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"error": "Lesson not found", "code": "LESSON_NOT_FOUND"})

    questions = (
        (
            await db.execute(
                select(QuizQuestion).where(QuizQuestion.lesson_id == lesson_id).order_by(QuizQuestion.id.asc()).limit(5)
            )
        )
        .scalars()
        .all()
    )
    if not questions:
        raise HTTPException(status_code=400, detail={"error": "No quiz questions for this lesson", "code": "QUIZ_EMPTY"})

    if len(payload.answers) != len(questions):
        raise HTTPException(
            status_code=400,
            detail={"error": "Answers count does not match number of questions", "code": "INVALID_ANSWERS"},
        )

    correct = 0
    correct_answers = []
    explanations = []
    for i, question in enumerate(questions):
        selected = payload.answers[i]
        is_correct = selected == question.correct_index
        if is_correct:
            correct += 1
        correct_answers.append(
            {
                "questionId": question.id,
                "selectedIndex": selected,
                "correctIndex": question.correct_index,
                "isCorrect": is_correct,
                "explanation": question.explanation,
            }
        )
        explanations.append({"questionId": question.id, "explanation": question.explanation})

    max_score = len(questions)
    score_percent = round((correct / max_score) * 100) if max_score else 0

    if score_percent >= 90:
        stars = 3
    elif score_percent >= 70:
        stars = 2
    elif score_percent >= 50:
        stars = 1
    else:
        stars = 0

    raw_xp = round((score_percent / 100) * lesson.xp_reward)
    progress = await get_or_create_progress(db, user.id, lesson.id)
    previous_xp = progress.xp_earned
    award_xp = max(raw_xp - previous_xp, 0)

    progress.status = "COMPLETED"
    progress.score = max(progress.score, score_percent)
    progress.xp_earned = max(progress.xp_earned, raw_xp)
    progress.completed_at = progress.completed_at or datetime.now(timezone.utc)

    if award_xp > 0:
        user.xp_total += award_xp

    update_streak(user)

    await db.commit()

    return {
        "score": correct,
        "maxScore": max_score,
        "xpEarned": award_xp,
        "stars": stars,
        "correctAnswers": correct_answers,
        "explanations": explanations,
    }

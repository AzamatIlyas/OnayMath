from __future__ import annotations

import ast
import math
import operator
from datetime import date, datetime, timedelta, timezone
from typing import Iterable, Sequence

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.education import AppUser, ChatMessage, City, Lesson, LessonProgress, School, Topic

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def parse_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        value = int(cursor)
        return max(value, 0)
    except ValueError:
        return 0


def paginate_list(items: Sequence, cursor: str | None, limit: int) -> tuple[list, str | None]:
    offset = parse_cursor(cursor)
    safe_limit = min(max(limit, 1), 100)
    page = list(items[offset : offset + safe_limit])
    next_cursor = str(offset + safe_limit) if offset + safe_limit < len(items) else None
    return page, next_cursor


def serialize_city(city: City) -> dict:
    return {
        "id": city.id,
        "name": city.name,
        "region": city.region,
    }


def serialize_school(school: School) -> dict:
    return {
        "id": school.id,
        "name": school.name,
        "cityId": school.city_id,
        "address": school.address,
    }


def serialize_user(user: AppUser) -> dict:
    role = user.role.upper()
    if role not in {"STUDENT", "TEACHER", "ADMIN"}:
        role = "STUDENT"

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatarUrl": user.avatar_url,
        "cityId": user.city_id,
        "schoolId": user.school_id,
        "grade": user.grade,
        "xpTotal": user.xp_total,
        "streakDays": user.streak_days,
        "lastActiveAt": user.last_active_at,
        "role": role,
        "emailVerified": user.email_verified,
        "createdAt": user.created_at,
        "updatedAt": user.updated_at,
    }


async def get_or_create_progress(session: AsyncSession, user_id: str, lesson_id: str) -> LessonProgress:
    query = select(LessonProgress).where(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
    existing = (await session.execute(query)).scalar_one_or_none()
    if existing:
        return existing

    progress = LessonProgress(user_id=user_id, lesson_id=lesson_id)
    session.add(progress)
    await session.flush()
    return progress


def serialize_progress(progress: LessonProgress | None) -> dict:
    if not progress:
        return {
            "status": "NOT_STARTED",
            "score": 0,
            "xpEarned": 0,
            "completedAt": None,
        }
    return {
        "status": progress.status,
        "score": progress.score,
        "xpEarned": progress.xp_earned,
        "completedAt": progress.completed_at,
    }


async def build_topic_summary(session: AsyncSession, topic: Topic, user_id: str) -> dict:
    lessons = (
        (
            await session.execute(
                select(Lesson).where(Lesson.topic_id == topic.id).order_by(Lesson.order_index.asc(), Lesson.id.asc())
            )
        )
        .scalars()
        .all()
    )
    lesson_ids = [lesson.id for lesson in lessons]

    progresses: dict[str, LessonProgress] = {}
    if lesson_ids:
        rows = (
            (
                await session.execute(
                    select(LessonProgress).where(
                        LessonProgress.user_id == user_id,
                        LessonProgress.lesson_id.in_(lesson_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        progresses = {row.lesson_id: row for row in rows}

    total_lessons = len(lessons)
    completed_lessons = sum(1 for lesson_id in lesson_ids if progresses.get(lesson_id) and progresses[lesson_id].status == "COMPLETED")
    progress_percent = round((completed_lessons / total_lessons) * 100) if total_lessons else 0

    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "grade": topic.grade,
        "order": topic.order_index,
        "iconUrl": topic.icon_url,
        "isPublished": topic.is_published,
        "progressPercent": progress_percent,
        "completedLessons": completed_lessons,
        "totalLessons": total_lessons,
        "lessons": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "order": lesson.order_index,
                "durationMinutes": lesson.duration_minutes,
                "progress": serialize_progress(progresses.get(lesson.id)),
            }
            for lesson in lessons
        ],
    }


async def get_user_stats(session: AsyncSession, user: AppUser) -> dict:
    lessons_done = (
        await session.execute(
            select(func.count())
            .select_from(LessonProgress)
            .where(LessonProgress.user_id == user.id, LessonProgress.status == "COMPLETED")
        )
    ).scalar_one()
    tests_passed = (
        await session.execute(
            select(func.count())
            .select_from(LessonProgress)
            .where(
                LessonProgress.user_id == user.id,
                LessonProgress.status == "COMPLETED",
                LessonProgress.score >= 60,
            )
        )
    ).scalar_one()

    return {
        "xpTotal": user.xp_total,
        "streakDays": user.streak_days,
        "lessonsDone": int(lessons_done or 0),
        "testsPassed": int(tests_passed or 0),
    }


def build_achievements(stats: dict, user: AppUser) -> list[dict]:
    now = datetime.now(timezone.utc)
    created_at = user.created_at or now
    unlocked: list[dict] = []

    if stats["lessonsDone"] >= 1:
        unlocked.append(
            {
                "id": "ach-first-lesson",
                "unlockedAt": created_at,
                "achievement": {
                    "id": "ach-first-lesson",
                    "title": "Первый шаг",
                    "description": "Завершите первый урок.",
                    "iconUrl": None,
                    "xpReward": 20,
                },
            }
        )
    if stats["testsPassed"] >= 3:
        unlocked.append(
            {
                "id": "ach-tests-3",
                "unlockedAt": now - timedelta(days=1),
                "achievement": {
                    "id": "ach-tests-3",
                    "title": "Тест-мастер",
                    "description": "Сдайте 3 теста с проходным баллом.",
                    "iconUrl": None,
                    "xpReward": 40,
                },
            }
        )
    if stats["xpTotal"] >= 300:
        unlocked.append(
            {
                "id": "ach-xp-300",
                "unlockedAt": now - timedelta(days=2),
                "achievement": {
                    "id": "ach-xp-300",
                    "title": "Сила практики",
                    "description": "Наберите 300 XP.",
                    "iconUrl": None,
                    "xpReward": 50,
                },
            }
        )
    if stats["streakDays"] >= 3:
        unlocked.append(
            {
                "id": "ach-streak-3",
                "unlockedAt": now,
                "achievement": {
                    "id": "ach-streak-3",
                    "title": "Серия побед",
                    "description": "Занимайтесь 3 дня подряд.",
                    "iconUrl": None,
                    "xpReward": 30,
                },
            }
        )

    return unlocked


def update_streak(user: AppUser) -> None:
    now = datetime.now(timezone.utc)
    today = now.date()

    if not user.last_active_at:
        user.streak_days = max(user.streak_days, 1)
        user.last_active_at = now
        return

    last_date = user.last_active_at.date()
    if last_date == today:
        user.last_active_at = now
        return

    if last_date == today - timedelta(days=1):
        user.streak_days = user.streak_days + 1
    else:
        user.streak_days = 1

    user.last_active_at = now


def _eval_expr(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](_eval_expr(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        left = _eval_expr(node.left)
        right = _eval_expr(node.right)
        return SAFE_OPERATORS[type(node.op)](left, right)
    raise ValueError("Unsupported expression")


def try_solve_expression(message: str) -> str | None:
    cleaned = message.replace("^", "**").strip()
    if not cleaned:
        return None

    if not any(ch.isdigit() for ch in cleaned):
        return None

    try:
        tree = ast.parse(cleaned, mode="eval")
        value = _eval_expr(tree.body)
        if math.isfinite(value):
            if value.is_integer():
                return str(int(value))
            return f"{value:.4f}".rstrip("0").rstrip(".")
        return None
    except Exception:
        return None


def build_assistant_reply(message: str, topic: Topic | None = None, history: Iterable[dict] | None = None) -> str:
    maybe_answer = try_solve_expression(message)
    if maybe_answer is not None:
        return (
            f"Результат вычисления: {maybe_answer}\n\n"
            "Как проверять себя:\n"
            "1. Соблюдай порядок действий.\n"
            "2. Пересчитай выражение по шагам.\n"
            "3. Сверь знаки и скобки."
        )

    topic_line = f"Тема: {topic.title}\n" if topic else ""
    hint = ""
    lowered = message.lower()

    if "дроб" in lowered:
        hint = (
            "Алгоритм для дробей:\n"
            "1. Приведи к общему знаменателю.\n"
            "2. Выполни действие только с числителями.\n"
            "3. Сократи результат.\n"
        )
    elif "уравнен" in lowered:
        hint = (
            "Алгоритм для линейного уравнения:\n"
            "1. Перенеси неизвестные влево, числа вправо.\n"
            "2. Приведи подобные.\n"
            "3. Раздели на коэффициент перед x.\n"
            "4. Сделай проверку подстановкой.\n"
        )
    elif "геом" in lowered or "угол" in lowered or "треуг" in lowered:
        hint = (
            "Ключевые правила:\n"
            "1. Сумма углов треугольника = 180°.\n"
            "2. Вертикальные углы равны.\n"
            "3. Смежные углы дают 180°.\n"
        )
    else:
        hint = (
            "Разберем тему пошагово:\n"
            "1. Определи, что известно в задаче.\n"
            "2. Выбери формулу или правило.\n"
            "3. Решай по этапам без пропусков.\n"
            "4. Проверь ответ обратным действием.\n"
        )

    return (
        f"{topic_line}"
        "Объясняю коротко и понятно.\n\n"
        f"{hint}\n"
        "Если хочешь, отправь конкретный пример из задачи, и я разберу его до ответа."
    )


def split_text_chunks(text: str, chunk_size: int = 36) -> list[str]:
    if chunk_size <= 0:
        return [text]
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def serialize_chat_message(item: ChatMessage) -> dict:
    return {
        "id": item.id,
        "role": item.role,
        "content": item.content,
        "topicContext": item.topic_context,
        "createdAt": item.created_at,
    }

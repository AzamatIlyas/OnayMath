from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.db_config import Base


def _id() -> str:
    return uuid.uuid4().hex


class City(Base):
    __tablename__ = "cities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)

    schools: Mapped[list["School"]] = relationship(back_populates="city")
    users: Mapped[list["AppUser"]] = relationship(back_populates="city")


class School(Base):
    __tablename__ = "schools"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id"), nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    city: Mapped["City"] = relationship(back_populates="schools")
    users: Mapped[list["AppUser"]] = relationship(back_populates="school")


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city_id: Mapped[str | None] = mapped_column(ForeignKey("cities.id"), nullable=True, index=True)
    school_id: Mapped[str | None] = mapped_column(ForeignKey("schools.id"), nullable=True, index=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    xp_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="STUDENT")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    city: Mapped["City | None"] = relationship(back_populates="users")
    school: Mapped["School | None"] = relationship(back_populates="users")
    progresses: Mapped[list["LessonProgress"]] = relationship(back_populates="user")
    chats: Mapped[list["ChatMessage"]] = relationship(back_populates="user")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("grade", "order_index", name="uq_topics_grade_order"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    lessons: Mapped[list["Lesson"]] = relationship(back_populates="topic")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("topic_id", "order_index", name="uq_lessons_topic_order"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=40)

    topic: Mapped["Topic"] = relationship(back_populates="lessons")
    questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="lesson")
    progresses: Mapped[list["LessonProgress"]] = relationship(back_populates="lesson")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    lesson: Mapped["Lesson"] = relationship(back_populates="questions")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NOT_STARTED")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["AppUser"] = relationship(back_populates="progresses")
    lesson: Mapped["Lesson"] = relationship(back_populates="progresses")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    grade: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chapters: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("app_users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    topic_context: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    user: Mapped["AppUser"] = relationship(back_populates="chats")

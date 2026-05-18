from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class ApiErrorPayload(BaseModel):
    error: str
    code: str
    details: Any | None = None


class PaginatedResponse(BaseModel):
    data: list[Any]
    nextCursor: str | None = None


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    cityId: str
    schoolId: str
    grade: int = Field(ge=1, le=11)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str


class CityOut(BaseModel):
    id: str
    name: str
    region: str


class SchoolOut(BaseModel):
    id: str
    name: str
    cityId: str
    address: str | None = None


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    avatarUrl: str | None = None
    cityId: str | None = None
    schoolId: str | None = None
    grade: int
    xpTotal: int
    streakDays: int
    lastActiveAt: datetime | None = None
    role: Literal["STUDENT", "TEACHER", "ADMIN"]
    emailVerified: bool
    createdAt: datetime | None = None
    updatedAt: datetime | None = None


class AuthResponse(BaseModel):
    user: UserOut
    accessToken: str
    refreshToken: str


class UserStatsOut(BaseModel):
    xpTotal: int
    streakDays: int
    lessonsDone: int
    testsPassed: int


class UserWithStatsOut(UserOut):
    city: CityOut | None = None
    school: SchoolOut | None = None
    stats: UserStatsOut


class UpdateMeRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    avatarUrl: str | None = Field(default=None, max_length=500)
    grade: int | None = Field(default=None, ge=1, le=11)


class AchievementOut(BaseModel):
    id: str
    unlockedAt: datetime
    achievement: dict[str, Any]


class TopicProgressOut(BaseModel):
    status: Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]
    score: int
    xpEarned: int
    completedAt: datetime | None = None


class TopicLessonOut(BaseModel):
    id: str
    title: str
    order: int
    durationMinutes: int
    progress: TopicProgressOut


class TopicSummaryOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    grade: int
    order: int
    iconUrl: str | None = None
    isPublished: bool
    progressPercent: int
    completedLessons: int
    totalLessons: int


class TopicDetailOut(TopicSummaryOut):
    lessons: list[TopicLessonOut]


class LessonOut(BaseModel):
    id: str
    topicId: str
    title: str
    content: Any
    order: int
    durationMinutes: int
    progress: TopicProgressOut


class QuizQuestionOut(BaseModel):
    id: str
    text: str
    options: list[str]


class QuizQuestionsResponse(BaseModel):
    lessonId: str
    questions: list[QuizQuestionOut]


class QuizSubmitRequest(BaseModel):
    answers: list[int]


class QuizSubmitResultOut(BaseModel):
    score: int
    maxScore: int
    scorePercent: int
    passed: bool
    passingScorePercent: int
    xpEarned: int
    stars: int
    correctAnswers: list[dict[str, Any]]
    explanations: list[dict[str, Any]]


class LeaderboardEntryOut(BaseModel):
    rank: int
    xp: int
    user: dict[str, Any]


class LeaderboardResponseOut(BaseModel):
    scope: Literal["class", "school", "city"]
    leaderboard: list[LeaderboardEntryOut]
    currentUser: LeaderboardEntryOut | None = None


class BookOut(BaseModel):
    id: str
    title: str
    grade: int
    coverUrl: str | None = None
    fileUrl: str
    author: str | None = None
    publishedYear: int | None = None
    chapters: Any
    createdAt: datetime
    updatedAt: datetime


class BookDetailOut(BookOut):
    signedFileUrl: str


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    topicId: str | None = None
    conversationHistory: list[dict[str, str]] = Field(default_factory=list)


class ChatMessageOut(BaseModel):
    id: str
    role: Literal["USER", "ASSISTANT"]
    content: str
    topicContext: str | None = None
    createdAt: datetime

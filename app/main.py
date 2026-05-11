from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router.assistant import router as assistant_router
from app.api.router.auth import router as auth_router
from app.api.router.books import router as books_router
from app.api.router.leaderboard import router as leaderboard_router
from app.api.router.lessons import router as lessons_router
from app.api.router.locations import router as locations_router
from app.api.router.quizzes import router as quizzes_router
from app.api.router.topics import router as topics_router
from app.api.router.users import router as users_router
from app.core.settings import settings
from app.db.db_config import async_session_maker, engine
from app.db.seed import seed_all
from app.db.db_config import Base
from app.db.models import education as _education_models  # noqa: F401

app = FastAPI(title="OnayMath API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def on_http_exception(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        payload = {
            "error": exc.detail.get("error", "Сұраныс орындалмады"),
            "code": exc.detail.get("code", "HTTP_ERROR"),
            "details": exc.detail.get("details"),
        }
    else:
        payload = {"error": str(exc.detail), "code": "HTTP_ERROR", "details": None}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def on_validation_error(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Валидация қатесі",
            "code": "VALIDATION_ERROR",
            "details": exc.errors(),
        },
    )


@app.on_event("startup")
async def startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        await seed_all(session)


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(locations_router)
api_router.include_router(topics_router)
api_router.include_router(lessons_router)
api_router.include_router(quizzes_router)
api_router.include_router(leaderboard_router)
api_router.include_router(books_router)
api_router.include_router(assistant_router)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

from __future__ import annotations

import json
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, Book
from app.service.platform import paginate_list
from app.service.storage import build_book_signed_url, upload_book_pdf

router = APIRouter(prefix="/books", tags=["books"])


def serialize_book(book: Book) -> dict:
    return {
        "id": book.id,
        "title": book.title,
        "grade": book.grade,
        "coverUrl": book.cover_url,
        "fileUrl": book.file_url,
        "author": book.author,
        "publishedYear": book.published_year,
        "chapters": book.chapters,
        "createdAt": book.created_at,
        "updatedAt": book.updated_at,
    }


def _slug_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    cleaned = cleaned.strip("-._")
    return cleaned or "book"


def _parse_chapters(raw: str | None) -> list[str]:
    if raw is None or not raw.strip():
        return []

    text = raw.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            result: list[str] = []
            for item in parsed:
                value = str(item).strip()
                if value:
                    result.append(value)
            return result
    except Exception:
        pass

    items = [chunk.strip() for chunk in re.split(r"[\n,;]+", text)]
    return [item for item in items if item]


@router.get("/")
async def get_books(
    grade: int | None = Query(default=None, ge=1, le=11),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = user
    query = select(Book).order_by(Book.grade.asc(), Book.title.asc())
    if grade is not None:
        query = query.where(Book.grade == grade)
    books = (await db.execute(query)).scalars().all()
    items = [serialize_book(book) for book in books]
    page, next_cursor = paginate_list(items, cursor, limit)
    return {"data": page, "nextCursor": next_cursor}


@router.post("/upload")
async def upload_book(
    title: str = Form(...),
    grade: int = Form(...),
    file: UploadFile = File(...),
    bookId: str | None = Form(default=None),
    author: str | None = Form(default=None),
    publishedYear: int | None = Form(default=None),
    chapters: str | None = Form(default=None),
    coverUrl: str | None = Form(default=None),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _ = user

    if grade < 1 or grade > 11:
        raise HTTPException(status_code=400, detail={"error": "Сынып 1 мен 11 аралығында болуы керек", "code": "INVALID_GRADE"})

    filename = file.filename or ""
    content_type = (file.content_type or "").lower()
    if not filename.lower().endswith(".pdf") and content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail={"error": "Тек PDF файлын жүктеуге болады", "code": "INVALID_FILE_TYPE"})

    safe_title = title.strip()
    if not safe_title:
        raise HTTPException(status_code=400, detail={"error": "Кітап атауы бос болмауы керек", "code": "INVALID_TITLE"})

    book_id = (bookId or "").strip() or f"book-{uuid4().hex[:12]}"
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    safe_name = _slug_filename(stem)
    object_key = f"grade-{grade}/uploads/{book_id}-{safe_name}.pdf"

    try:
        uploaded_url = await run_in_threadpool(upload_book_pdf, file.file, object_key, "application/pdf")
    except RuntimeError:
        raise HTTPException(status_code=503, detail={"error": "Cloudflare R2 бапталмаған", "code": "R2_NOT_CONFIGURED"}) from None
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "Кітап файлын жүктеу сәтсіз аяқталды", "code": "R2_UPLOAD_FAILED"}) from None

    book = await db.get(Book, book_id)
    if not book:
        book = Book(
            id=book_id,
            title=safe_title,
            grade=grade,
            cover_url=coverUrl.strip() if coverUrl and coverUrl.strip() else None,
            file_url=uploaded_url,
            author=author.strip() if author and author.strip() else None,
            published_year=publishedYear,
            chapters=_parse_chapters(chapters),
        )
        db.add(book)
    else:
        book.title = safe_title
        book.grade = grade
        book.cover_url = coverUrl.strip() if coverUrl and coverUrl.strip() else None
        book.file_url = uploaded_url
        book.author = author.strip() if author and author.strip() else None
        book.published_year = publishedYear
        book.chapters = _parse_chapters(chapters)

    await db.commit()
    await db.refresh(book)

    payload = serialize_book(book)
    payload["signedFileUrl"] = build_book_signed_url(book.file_url)
    return payload


@router.get("/{book_id}")
async def get_book(book_id: str, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    _ = user
    book = (await db.execute(select(Book).where(Book.id == book_id))).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail={"error": "Кітап табылмады", "code": "BOOK_NOT_FOUND"})

    payload = serialize_book(book)
    payload["signedFileUrl"] = build_book_signed_url(book.file_url)
    return payload

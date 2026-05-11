from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.db.models.education import AppUser, Book
from app.service.platform import paginate_list
from app.service.storage import build_book_signed_url

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


@router.get("/")
async def get_books(
    grade: int | None = Query(default=None, ge=1, le=11),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    user: AppUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Book).order_by(Book.grade.asc(), Book.title.asc())
    if grade is not None:
        query = query.where(Book.grade == grade)
    books = (await db.execute(query)).scalars().all()
    items = [serialize_book(book) for book in books]
    page, next_cursor = paginate_list(items, cursor, limit)
    return {"data": page, "nextCursor": next_cursor}


@router.get("/{book_id}")
async def get_book(book_id: str, user: AppUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    book = (await db.execute(select(Book).where(Book.id == book_id))).scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail={"error": "Кітап табылмады", "code": "BOOK_NOT_FOUND"})

    payload = serialize_book(book)
    payload["signedFileUrl"] = build_book_signed_url(book.file_url)
    return payload

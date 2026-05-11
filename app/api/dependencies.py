from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token_safely
from app.db.db_config import async_session_maker
from app.db.models.education import AppUser


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail={"error": "Missing authorization token", "code": "UNAUTHORIZED"})
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail={"error": "Invalid authorization scheme", "code": "UNAUTHORIZED"})
    return authorization.split(" ", 1)[1].strip()


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AppUser:
    token = _extract_bearer_token(authorization)
    payload = decode_token_safely(token, refresh=False)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={"error": "Invalid access token", "code": "UNAUTHORIZED"})

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail={"error": "Invalid access token", "code": "UNAUTHORIZED"})

    user = (await db.execute(select(AppUser).where(AppUser.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail={"error": "User not found", "code": "UNAUTHORIZED"})
    return user

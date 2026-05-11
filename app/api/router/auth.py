from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token_safely,
    hash_password,
    verify_password,
)
from app.db.models.education import AppUser, School
from app.schema.api import AuthResponse, LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest
from app.service.platform import serialize_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(AppUser).where(AppUser.email == payload.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail={"error": "Email already registered", "code": "EMAIL_EXISTS"})

    school = (await db.execute(select(School).where(School.id == payload.schoolId))).scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail={"error": "School not found", "code": "SCHOOL_NOT_FOUND"})
    if school.city_id != payload.cityId:
        raise HTTPException(status_code=400, detail={"error": "School does not belong to selected city", "code": "INVALID_LOCATION"})

    user = AppUser(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        name=payload.name.strip(),
        city_id=payload.cityId,
        school_id=payload.schoolId,
        grade=payload.grade,
        role="STUDENT",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return {
        "user": serialize_user(user),
        "accessToken": access_token,
        "refreshToken": refresh_token,
    }


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(AppUser).where(AppUser.email == payload.email.lower()))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"error": "Invalid email or password", "code": "INVALID_CREDENTIALS"})

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return {
        "user": serialize_user(user),
        "accessToken": access_token,
        "refreshToken": refresh_token,
    }


@router.post("/refresh")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_payload = decode_token_safely(payload.refreshToken, refresh=True)
    if not token_payload or token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={"error": "Invalid refresh token", "code": "UNAUTHORIZED"})

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail={"error": "Invalid refresh token", "code": "UNAUTHORIZED"})

    user = (await db.execute(select(AppUser).where(AppUser.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail={"error": "User not found", "code": "UNAUTHORIZED"})

    return {"accessToken": create_access_token(user.id)}


@router.post("/logout")
async def logout(payload: LogoutRequest):
    if not payload.refreshToken:
        raise HTTPException(status_code=400, detail={"error": "Missing refresh token", "code": "BAD_REQUEST"})
    return {"success": True}

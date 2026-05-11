from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _create_token(data: dict[str, Any], secret_key: str, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, secret_key, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _create_token({"sub": user_id, "type": "access"}, settings.ACCESS_TOKEN_SECRET_KEY, timedelta(hours=1))


def create_refresh_token(user_id: str) -> str:
    return _create_token({"sub": user_id, "type": "refresh"}, settings.REFRESH_TOKEN_SECRET_KEY, timedelta(days=14))


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.ACCESS_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM])


def decode_refresh_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM])


def decode_token_safely(token: str, refresh: bool = False) -> dict[str, Any] | None:
    try:
        if refresh:
            return decode_refresh_token(token)
        return decode_access_token(token)
    except JWTError:
        return None

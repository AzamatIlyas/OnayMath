from fastapi import HTTPException, Response
import re
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import EmailStr
from app.core.settings import settings

from app.service.user import UserService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.ACCESS_TOKEN_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, key: str):
    try:
        payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
    





class AuthService:

    @classmethod
    async def register(cls, first_name: str, last_name, email: EmailStr, password: str):

        # if not cls.verify_password_from_scripts(password):
        #     raise HTTPException(status_code=400)


        existing_user = await UserService.get_user_by_email(email=email)

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = pwd_context.hash(password)
        return await UserService.create_user(first_name=first_name, last_name=last_name, email=email, password=hashed_password)
    
    @classmethod
    async def login(cls, response: Response, email: str, password: str):
        existing_user = await UserService.get_user_by_email(email=email)

        if not existing_user or not verify_password(password, existing_user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # if not cls.verify_password_from_scripts(password):
        #     raise HTTPException(status_code=400)

        access_token = create_access_token({"sub": str(existing_user.id)})
        refresh_token = create_refresh_token({"sub": str(existing_user.id)})

        response.set_cookie("access_token", access_token, httponly=True)
        response.set_cookie("refresh_token", refresh_token, httponly=True)
        return {"message": "Successfully logged in"}
    

    @classmethod
    async def logout(cls, response: Response):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return {"message": "Successfully logged out"}
    

    @classmethod
    async def refresh(cls, response: Response, refresh_token: str):
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Missing refresh token")

        try:
            payload = jwt.decode(refresh_token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid refresh token 1")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token 2")

        access_token = create_access_token({"sub": str(user_id)})
        refresh_token = create_refresh_token({"sub": str(user_id)})

        response.set_cookie("access_token", access_token, httponly=True)
        response.set_cookie("refresh_token", refresh_token, httponly=True)

        return {"message": "Successfully refreshed"}
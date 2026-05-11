
from fastapi import HTTPException
from app.db.repo.user import UserDAO
from app.schema.user import SUserResponse
from app.db.models.user import User


class UserService:

    @classmethod
    async def get_all_users(cls):
        return await UserDAO.get_all()

    @classmethod
    async def get_user_by_email(cls, email: str) -> User:
        return await UserDAO.get_user_by_email(email)
    
    @classmethod
    async def create_user(cls, first_name: str, last_name: str, email: str, password: str):
        return await UserDAO.create(
            first_name=first_name, 
            last_name=last_name,
            email=email, 
            password=password
            )

    @classmethod
    async def get_user_by_id(cls, id: int) -> SUserResponse:
        return await UserDAO.get_by_id(id=id)
    
    # @classmethod
    # async def update_user(cls, user_id: int, data: SUserUpdate):
    #     return await UserDAO.update_user(id=user_id, data=data)
    
    @classmethod
    async def get_user_profile(cls, user_id: int) -> SUserResponse:
        return await UserDAO.get_user_profile(user_id=user_id)
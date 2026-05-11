from fastapi import APIRouter, Depends, Response, HTTPException

from app.schema.user import SUserRegistration, SLogin, SUserResponse
from app.service.user import UserService
# from app.service.auth import AuthService
from app.api.dependencies import get_current_user
from app.auth.auth import AuthService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/register")
async def register_user(user: SUserRegistration):
    return await AuthService.register(
            email=user.email, 
            password=user.password,
            first_name=user.first_name,
            last_name=user.last_name
        )

@router.post("/login")
async def login_user(response: Response, user: SLogin):
    return await AuthService.login(response=response, email=user.email, password=user.password)

@router.post("/logout")
async def logout_user(response: Response, user: SUserResponse = Depends(get_current_user)):
    return await AuthService.logout(response=response)


@router.get("/", response_model=list[SUserResponse])
async def get_all_users():
    return await UserService.get_all_users()



# @router.patch("/update")
# async def update_user(data: SUserUpdate, user: SUserResponse = Depends(get_current_user)):
#     return await UserService.update_user(data=data, user_id=user.id)

@router.get("/profile", response_model=SUserResponse)
async def get_user_profile(user: SUserResponse = Depends(get_current_user)):
    return user
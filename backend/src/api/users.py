from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from src.api.dependencies import AuthServiceDep, CurrentAdmin, CurrentUser
from src.schemas import RefreshTokenRequest, UserCreate, UserRoleUpdate, UserSchema

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: AuthServiceDep):
    return await service.register(user)


@router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], service: AuthServiceDep
):
    return await service.login(form_data)


@router.put("/{user_id}/role", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: int, role: UserRoleUpdate, service: AuthServiceDep, admin: CurrentAdmin
):
    return await service.update_role(user_id, role, admin)


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: CurrentUser):
    return current_user


@router.post("/refresh-token")
async def refresh_token(body: RefreshTokenRequest, service: AuthServiceDep):
    return await service.refresh_token(body)


@router.post("/access-token")
async def refresh_access_token(body: RefreshTokenRequest, service: AuthServiceDep):
    return await service.refresh_access_token(body)

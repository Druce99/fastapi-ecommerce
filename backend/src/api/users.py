from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.security import get_current_admin, get_current_user
from src.models import UserModel
from src.schemas import RefreshTokenRequest, UserCreate, UserRoleUpdate, UserSchema
from src.service.auth import AuthService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    return await AuthService(db).register(user)


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
):
    return await AuthService(db).login(form_data)


@router.put("/{user_id}/role", response_model=UserSchema, status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: int,
    role: UserRoleUpdate,
    db: AsyncSession = Depends(get_async_db),
    admin: UserModel = Depends(get_current_admin),
):
    return await AuthService(db).update_role(user_id, role, admin)


@router.get("/me", response_model=UserSchema)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    return current_user


@router.post("/refresh-token")
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    return await AuthService(db).refresh_token(body)


@router.post("/access-token")
async def refresh_access_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)):
    return await AuthService(db).refresh_access_token(body)

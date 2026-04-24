import jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from src.models import UserModel
from src.repository.users import UserRepository
from src.schemas import RefreshTokenRequest, UserCreate, UserRoleUpdate


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repo = UserRepository(db)
        self.db = db

    async def register(self, user_data: UserCreate) -> UserModel:
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = await self.user_repo.create(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            role=user_data.role,
        )
        await self.db.commit()
        return user

    async def login(self, form_data: OAuth2PasswordRequestForm) -> dict:
        user = await self.user_repo.get_active_by_email(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        data = {"sub": user.email, "role": user.role, "id": user.id}
        return {
            "access_token": create_access_token(data),
            "refresh_token": create_refresh_token(data),
            "token_type": "bearer",
        }

    async def update_role(self, user_id: int, role_data: UserRoleUpdate, admin: UserModel) -> UserModel:
        user = await self.user_repo.get_active_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.role == "admin" and user.id != admin.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change role of another administrator",
            )
        if user.id == admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role",
            )
        updated = await self.user_repo.update_role(user_id, role_data.role)
        await self.db.commit()
        return updated

    async def refresh_token(self, body: RefreshTokenRequest) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str | None = payload.get("sub")
            token_type: str | None = payload.get("token_type")
            if email is None or token_type != "refresh":
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception

        user = await self.user_repo.get_active_by_email(email)
        if not user:
            raise credentials_exception

        return {
            "refresh_token": create_refresh_token({"sub": user.email, "role": user.role, "id": user.id}),
            "token_type": "bearer",
        }

    async def refresh_access_token(self, body: RefreshTokenRequest) -> dict:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_type: str | None = payload.get("token_type")
            user_id: int | None = payload.get("id")
            if token_type != "refresh" or user_id is None:
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception

        user = await self.user_repo.get_active_by_id(user_id)
        if not user:
            raise credentials_exception

        return {
            "access_token": create_access_token({"sub": user.email, "role": user.role, "id": user.id}),
            "token_type": "bearer",
        }

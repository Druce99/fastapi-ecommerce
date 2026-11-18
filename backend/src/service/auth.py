import jwt
from anyio import to_thread
from fastapi.security import OAuth2PasswordRequestForm
from src.core.broker import publish_event
from src.core.config import settings
from src.core.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    EmailAlreadyRegisteredError,
    NotFoundError,
    PermissionDeniedError,
)
from src.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from src.models import UserModel
from src.repository.uow import UnitOfWorkFactory
from src.schemas import RefreshTokenRequest, UserCreate, UserRegisteredSchema, UserRoleUpdate

# Фиктивный хеш: проверяется, когда пользователь не найден, чтобы время ответа не выдавало,
# зарегистрирован ли email.
_DUMMY_HASH = hash_password("dummy-password-for-constant-time-login")


class AuthService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def register(self, user_data: UserCreate) -> UserModel:
        # bcrypt тяжёлый и синхронный: выносим в поток, чтобы не блокировать event loop
        hashed_password = await to_thread.run_sync(hash_password, user_data.password)

        async with self._uow_factory() as uow:
            if await uow.users.get_by_email(user_data.email):
                raise EmailAlreadyRegisteredError
            user = await uow.users.create(
                email=user_data.email,
                hashed_password=hashed_password,
                role=user_data.role,
            )
            await uow.commit()

        await publish_event(UserRegisteredSchema(email=user.email), channel="user_registered")
        return user

    async def login(self, form_data: OAuth2PasswordRequestForm) -> dict:
        async with self._uow_factory() as uow:
            user = await uow.users.get_active_by_email(form_data.username)

        password_hash = user.hashed_password if user else _DUMMY_HASH
        password_ok = await to_thread.run_sync(verify_password, form_data.password, password_hash)
        if not user or not password_ok:
            raise AuthenticationError("Incorrect email or password")
        data = {"sub": user.email, "role": user.role, "id": user.id}
        return {
            "access_token": create_access_token(data),
            "refresh_token": create_refresh_token(data),
            "token_type": "bearer",
        }

    async def update_role(
        self, user_id: int, role_data: UserRoleUpdate, admin: UserModel
    ) -> UserModel:
        async with self._uow_factory() as uow:
            user = await uow.users.get_active_by_id(user_id)
            if not user:
                raise NotFoundError("User not found")
            if user.role == "admin" and user.id != admin.id:
                raise PermissionDeniedError("Cannot change role of another administrator")
            if user.id == admin.id:
                raise BusinessRuleError("Cannot change your own role")
            updated = await uow.users.update_role(user_id, role_data.role)
            await uow.commit()
        return updated

    async def refresh_token(self, body: RefreshTokenRequest) -> dict:
        credentials_exception = AuthenticationError("Could not validate refresh token")
        try:
            payload = jwt.decode(
                body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except jwt.InvalidTokenError as exc:
            raise credentials_exception from exc

        email: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")
        if email is None or token_type != "refresh":
            raise credentials_exception

        async with self._uow_factory() as uow:
            user = await uow.users.get_active_by_email(email)
        if not user:
            raise credentials_exception

        return {
            "refresh_token": create_refresh_token(
                {"sub": user.email, "role": user.role, "id": user.id}
            ),
            "token_type": "bearer",
        }

    async def refresh_access_token(self, body: RefreshTokenRequest) -> dict:
        credentials_exception = AuthenticationError("Invalid or expired refresh token")
        try:
            payload = jwt.decode(
                body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except jwt.InvalidTokenError as exc:
            raise credentials_exception from exc

        token_type: str | None = payload.get("token_type")
        user_id: int | None = payload.get("id")
        if token_type != "refresh" or user_id is None:
            raise credentials_exception

        async with self._uow_factory() as uow:
            user = await uow.users.get_active_by_id(user_id)
        if not user:
            raise credentials_exception

        return {
            "access_token": create_access_token(
                {"sub": user.email, "role": user.role, "id": user.id}
            ),
            "token_type": "bearer",
        }

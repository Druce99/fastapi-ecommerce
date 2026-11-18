"""Зависимости FastAPI: единое место сборки сервисов и получения текущего пользователя."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from src.core.config import settings
from src.core.exceptions import AuthenticationError, PermissionDeniedError
from src.models import UserModel
from src.repository.uow import SqlAlchemyUnitOfWork, UnitOfWorkFactory
from src.service.auth import AuthService
from src.service.cart import CartService
from src.service.categories import CategoryService
from src.service.orders import OrderService
from src.service.products import ProductService
from src.service.reviews import ReviewService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")


# ========== Unit of Work ==========
def get_uow_factory() -> UnitOfWorkFactory:
    """Фабрика UoW. В тестах подменяется через `app.dependency_overrides`."""
    return SqlAlchemyUnitOfWork


UowFactoryDep = Annotated[UnitOfWorkFactory, Depends(get_uow_factory)]


# ========== Сервисы ==========
def get_auth_service(uow_factory: UowFactoryDep) -> AuthService:
    return AuthService(uow_factory)


def get_cart_service(uow_factory: UowFactoryDep) -> CartService:
    return CartService(uow_factory)


def get_category_service(uow_factory: UowFactoryDep) -> CategoryService:
    return CategoryService(uow_factory)


def get_order_service(uow_factory: UowFactoryDep) -> OrderService:
    return OrderService(uow_factory)


def get_product_service(uow_factory: UowFactoryDep) -> ProductService:
    return ProductService(uow_factory)


def get_review_service(uow_factory: UowFactoryDep) -> ReviewService:
    return ReviewService(uow_factory)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CartServiceDep = Annotated[CartService, Depends(get_cart_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
ReviewServiceDep = Annotated[ReviewService, Depends(get_review_service)]


# ========== Текущий пользователь ==========
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], uow_factory: UowFactoryDep
) -> UserModel:
    """Проверяет JWT и возвращает активного пользователя из базы."""
    credentials_exception = AuthenticationError("Could not validate credentials")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise credentials_exception from exc

    email: str | None = payload.get("sub")
    token_type: str | None = payload.get("token_type")
    if email is None or token_type != "access":
        raise credentials_exception

    async with uow_factory() as uow:
        user = await uow.users.get_active_by_email(email)

    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]


# ========== Проверка ролей ==========
async def get_current_seller(current_user: CurrentUser) -> UserModel:
    if current_user.role != "seller":
        raise PermissionDeniedError("Only sellers can perform this action")
    return current_user


async def get_current_admin(current_user: CurrentUser) -> UserModel:
    if current_user.role != "admin":
        raise PermissionDeniedError("Only admins can perform this action")
    return current_user


async def get_current_buyer(current_user: CurrentUser) -> UserModel:
    if current_user.role != "buyer":
        raise PermissionDeniedError("Only buyers can perform this action")
    return current_user


CurrentSeller = Annotated[UserModel, Depends(get_current_seller)]
CurrentAdmin = Annotated[UserModel, Depends(get_current_admin)]
CurrentBuyer = Annotated[UserModel, Depends(get_current_buyer)]

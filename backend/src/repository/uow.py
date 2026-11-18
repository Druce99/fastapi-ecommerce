"""Unit of Work: единая граница транзакции.

Сервис открывает UoW через `async with`, работает с репозиториями и явно вызывает
`commit()`. Если внутри блока возникло исключение, транзакция откатывается.
Если `commit()` не вызван, изменения не сохраняются (сессия закрывается без фиксации).
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.core.database import async_session_maker
from src.repository.cart import CartRepository
from src.repository.categories import CategoryRepository
from src.repository.orders import OrderRepository
from src.repository.products import ProductRepository
from src.repository.reviews import ReviewRepository
from src.repository.users import UserRepository


class AbstractUnitOfWork(ABC):
    """Интерфейс UoW: от него зависят сервисы (принцип инверсии зависимостей)."""

    users: UserRepository
    categories: CategoryRepository
    products: ProductRepository
    reviews: ReviewRepository
    cart: CartRepository
    orders: OrderRepository

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        # Откат только при ошибке. После успешного commit() rollback не нужен
        # и «протушил» бы уже загруженные объекты, которые сервис возвращает.
        if exc_type is not None:
            await self.rollback()

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...


# Фабрика UoW: сервис вызывает её на каждую транзакцию (в checkout их несколько).
UnitOfWorkFactory = Callable[[], AbstractUnitOfWork]


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] = async_session_maker
    ) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self._session_factory()
        self.users = UserRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.products = ProductRepository(self.session)
        self.reviews = ReviewRepository(self.session)
        self.cart = CartRepository(self.session)
        self.orders = OrderRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc, tb)
        finally:
            await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

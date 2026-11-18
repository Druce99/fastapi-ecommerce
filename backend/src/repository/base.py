from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import Base


class BaseRepository[ModelType: Base]:
    """Базовый репозиторий с общими CRUD-методами.

    Контракт транзакций: любой метод, который меняет данные, делает `flush()`
    (чтобы получить id и увидеть изменения в рамках текущей транзакции),
    но НИКОГДА не вызывает `commit()` / `rollback()`. Границу транзакции
    определяет вызывающий код (сервис).
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> ModelType | None:
        """Получить любую запись по ID."""
        result = await self.db.scalars(select(self.model).where(self.model.id == id))
        return result.first()

    async def get_active_by_id(self, id: int) -> ModelType | None:
        """Получить только активную запись по ID."""
        if not hasattr(self.model, "is_active"):
            return await self.get_by_id(id)

        result = await self.db.scalars(
            select(self.model).where(
                self.model.id == id,
                self.model.is_active.is_(True),
            )
        )
        return result.first()

    async def get_all_active(self, skip: int, limit: int) -> list[ModelType]:
        """Получить список активных записей, отсортированных по id."""
        query = select(self.model)

        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active.is_(True))

        query = query.order_by(self.model.id).offset(skip).limit(limit)
        result = await self.db.scalars(query)
        return list(result.all())

    # ========== Изменение данных (flush без commit) ==========

    async def add(self, instance: ModelType) -> ModelType:
        """Добавить готовый объект модели."""
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def create(self, **kwargs: Any) -> ModelType:
        """Создать новую запись."""
        return await self.add(self.model(**kwargs))

    async def update(self, id: int, update_data: dict[str, Any]) -> ModelType | None:
        """Обновить только активную запись."""
        instance = await self.get_active_by_id(id)
        if not instance:
            return None

        await self.db.execute(update(self.model).where(self.model.id == id).values(**update_data))
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete_logical(self, id: int) -> ModelType | None:
        """Логическое удаление: is_active = False."""
        if not hasattr(self.model, "is_active"):
            return None

        instance = await self.get_active_by_id(id)
        if not instance:
            return None

        await self.db.execute(update(self.model).where(self.model.id == id).values(is_active=False))
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete_physical(self, id: int) -> bool:
        """Физическое удаление записи."""
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base

# Переменная типа для модели SQLAlchemy
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Базовый репозиторий с общими CRUD-методами."""

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
                self.model.is_active == True,
            )
        )
        return result.first()

    async def get_all_active(
        self, skip: int, limit: int, order_by: str | None = None, descending: bool = False
    ) -> list[ModelType]:
        """Получить список активных записей."""
        query = select(self.model)

        if hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)

        if order_by:
            order_field = getattr(self.model, order_by, None)
            if order_field:
                query = query.order_by(order_field.desc() if descending else order_field)

        query = query.offset(skip).limit(limit)
        result = await self.db.scalars(query)
        return result.all()

    # ========== CRUD операции ==========

    async def add(self, instance: ModelType) -> ModelType:
        """Добавить запись."""
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def create(self, **kwargs: Any) -> ModelType:
        """Создать новую запись."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def create_from_schema(self, schema: Any) -> ModelType:
        """Создать запись из Pydantic схемы."""
        return await self.create(**schema.model_dump())

    async def update(self, id: int, update_data: dict[str, Any]) -> ModelType | None:
        """Обновить только активную запись."""
        instance = await self.get_active_by_id(id)
        if not instance:
            return None

        await self.db.execute(
            update(self.model).where(self.model.id == id).values(**update_data)
        )
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update_from_schema(self, id: int, schema: Any, exclude_unset: bool = True) -> ModelType | None:
        """Обновить запись из Pydantic схемы."""
        update_data = schema.model_dump(exclude_unset=exclude_unset)
        return await self.update(id, update_data)

    async def delete_logical(self, id: int) -> ModelType | None:
        """Логическое удаление (без commit)."""
        if not hasattr(self.model, "is_active"):
            return None

        instance = await self.get_active_by_id(id)
        if not instance:
            return None

        await self.db.execute(
            update(self.model).where(self.model.id == id).values(is_active=False)
        )
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

    async def restore(self, id: int) -> ModelType | None:
        """Восстановить логически удалённую запись."""
        if not hasattr(self.model, "is_active"):
            return None

        result = await self.db.scalars(
            select(self.model).where(self.model.id == id, self.model.is_active == False)
        )
        instance = result.first()
        if not instance:
            return None

        await self.db.execute(
            update(self.model).where(self.model.id == id).values(is_active=True)
        )
        await self.db.flush()
        instance.is_active = True
        return instance

    # ========== Вспомогательные методы ==========

    async def exists(self, id: int) -> bool:
        """Проверить существование записи."""
        result = await self.db.scalars(
            select(self.model.id).where(self.model.id == id).limit(1)
        )
        return result.first() is not None

    async def exists_active(self, id: int) -> bool:
        """Проверить существование активной записи."""
        if not hasattr(self.model, "is_active"):
            return await self.exists(id)

        result = await self.db.scalars(
            select(self.model.id).where(self.model.id == id, self.model.is_active == True).limit(1)
        )
        return result.first() is not None

    async def count(self, active_only: bool = False) -> int:
        """Получить количество записей."""
        query = select(func.count()).select_from(self.model)

        if active_only and hasattr(self.model, "is_active"):
            query = query.where(self.model.is_active == True)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_field(self, field_name: str, value: Any) -> ModelType | None:
        """Получить запись по любому полю."""
        field = getattr(self.model, field_name, None)
        if not field:
            return None
        result = await self.db.scalars(select(self.model).where(field == value))
        return result.first()

    async def get_all_by_field(self, field_name: str, value: Any, skip: int, limit: int) -> list[ModelType]:
        """Получить список записей по любому полю."""
        field = getattr(self.model, field_name, None)
        if not field:
            return []

        query = select(self.model).where(field == value).offset(skip).limit(limit)
        result = await self.db.scalars(query)
        return result.all()
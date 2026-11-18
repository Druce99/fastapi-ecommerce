from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import CategoryModel

from .base import BaseRepository


class CategoryRepository(BaseRepository[CategoryModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CategoryModel, db)

    async def get_by_name(self, name: str) -> CategoryModel | None:
        """Получить категорию по названию (включая неактивные)."""
        result = await self.db.scalars(select(self.model).where(self.model.name == name))
        return result.first()

    async def get_active_children(self, parent_id: int) -> list[CategoryModel]:
        """Получить только активные дочерние категории."""
        result = await self.db.scalars(
            select(self.model).where(
                self.model.parent_id == parent_id,
                self.model.is_active.is_(True),
            )
        )
        return list(result.all())

    async def get_root_categories(self) -> list[CategoryModel]:
        """Получить все корневые категории (без родителя)."""
        result = await self.db.scalars(
            select(self.model).where(
                self.model.parent_id.is_(None),
                self.model.is_active.is_(True),
            )
        )
        return list(result.all())

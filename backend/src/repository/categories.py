from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import CategoryModel

from .base import BaseRepository


class CategoryRepository(BaseRepository[CategoryModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CategoryModel, db)

    async def get_by_name(self, name: str) -> CategoryModel | None:
        """Получить категорию по названию."""
        return await self.get_by_field("name", name)

    async def get_children(self, parent_id: int) -> list[CategoryModel]:
        """Получить все дочерние категории (включая неактивные)."""
        result = await self.db.scalars(
            select(self.model).where(self.model.parent_id == parent_id)
        )
        return result.all()

    async def get_active_children(self, parent_id: int) -> list[CategoryModel]:
        """Получить только активные дочерние категории."""
        result = await self.db.scalars(
            select(self.model).where(
                self.model.parent_id == parent_id,
                self.model.is_active == True,
            )
        )
        return result.all()

    async def get_parent(self, category_id: int) -> CategoryModel | None:
        """Получить родительскую категорию."""
        category = await self.get_active_by_id(category_id)
        if not category or category.parent_id is None:
            return None
        return await self.get_active_by_id(category.parent_id)

    async def get_tree(self) -> list[CategoryModel]:
        """Получить все активные категории, отсортированные по родителю."""
        return await self.get_all_active(skip=0, limit=10000, order_by="parent_id")

    async def get_root_categories(self) -> list[CategoryModel]:
        """Получить все корневые категории (без родителя)."""
        result = await self.db.scalars(
            select(self.model).where(
                self.model.parent_id == None,
                self.model.is_active == True,
            )
        )
        return result.all()
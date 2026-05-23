from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import CategoryModel
from src.repository.categories import CategoryRepository
from src.schemas import CategoryCreate


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CategoryRepository(db)
        self.db = db

    async def get_all(self) -> list[CategoryModel]:
        """Получить все активные категории."""
        return await self.repo.get_all_active(skip=0, limit=10000, order_by="id")

    async def get_by_id(self, category_id: int) -> CategoryModel:
        """Получить категорию по ID."""
        category = await self.repo.get_active_by_id(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    async def create(self, category_data: CategoryCreate) -> CategoryModel:
        """Создать новую категорию."""
        existing = await self.repo.get_by_name(category_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists",
            )

        if category_data.parent_id is not None:
            parent = await self.repo.get_active_by_id(category_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found",
                )

        category = await self.repo.create(**category_data.model_dump())
        await self.db.commit()
        return category

    async def update(self, category_id: int, category_data: CategoryCreate) -> CategoryModel:
        """Обновить категорию."""
        existing = await self.repo.get_active_by_id(category_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        if category_data.name != existing.name:
            name_existing = await self.repo.get_by_name(category_data.name)
            if name_existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category with this name already exists",
                )

        if category_data.parent_id is not None:
            parent = await self.repo.get_active_by_id(category_data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent category not found",
                )

        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent",
            )

        update_data = category_data.model_dump(exclude_unset=True)
        updated = await self.repo.update(category_id, update_data)

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found after update",
            )

        await self.db.commit()
        return updated

    async def delete(self, category_id: int) -> CategoryModel:
        """Логическое удаление категории."""
        existing = await self.repo.get_active_by_id(category_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        children = await self.repo.get_active_children(category_id)
        if children:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with children. Delete children first.",
            )

        deleted = await self.repo.delete_logical(category_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found after delete",
            )

        await self.db.commit()
        return deleted

    async def get_root_categories(self) -> list[CategoryModel]:
        """Получить все корневые категории (без родителя)."""
        return await self.repo.get_root_categories()

    async def get_category_tree(self, category_id: int | None = None) -> dict:
        """Получить дерево категорий."""
        if category_id:
            category = await self.get_by_id(category_id)
            children = await self.repo.get_active_children(category_id)
        else:
            category = None
            children = await self.repo.get_root_categories()

        return {
            "category": category,
            "children": [
                await self.get_category_tree(child.id) for child in children
            ] if children else [],
        }
from src.core.exceptions import BusinessRuleError, NotFoundError
from src.models import CategoryModel
from src.repository.uow import AbstractUnitOfWork, UnitOfWorkFactory
from src.schemas import CategoryCreate


class CategoryService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_all(self) -> list[CategoryModel]:
        """Получить все активные категории."""
        async with self._uow_factory() as uow:
            return await uow.categories.get_all_active(skip=0, limit=10000)

    async def get_by_id(self, category_id: int) -> CategoryModel:
        """Получить категорию по ID."""
        async with self._uow_factory() as uow:
            return await self._get_active(uow, category_id)

    async def create(self, category_data: CategoryCreate) -> CategoryModel:
        """Создать новую категорию."""
        async with self._uow_factory() as uow:
            existing = await uow.categories.get_by_name(category_data.name)
            if existing:
                raise BusinessRuleError("Category with this name already exists")

            if category_data.parent_id is not None:
                parent = await uow.categories.get_active_by_id(category_data.parent_id)
                if not parent:
                    raise BusinessRuleError("Parent category not found")

            category = await uow.categories.create(**category_data.model_dump())
            await uow.commit()
        return category

    async def update(self, category_id: int, category_data: CategoryCreate) -> CategoryModel:
        """Обновить категорию."""
        async with self._uow_factory() as uow:
            existing = await self._get_active(uow, category_id)

            if category_data.name != existing.name:
                name_existing = await uow.categories.get_by_name(category_data.name)
                if name_existing:
                    raise BusinessRuleError("Category with this name already exists")

            if category_data.parent_id is not None:
                parent = await uow.categories.get_active_by_id(category_data.parent_id)
                if not parent:
                    raise BusinessRuleError("Parent category not found")

            if category_data.parent_id == category_id:
                raise BusinessRuleError("Category cannot be its own parent")

            update_data = category_data.model_dump(exclude_unset=True)
            updated = await uow.categories.update(category_id, update_data)
            if not updated:
                raise NotFoundError("Category not found after update")

            await uow.commit()
        return updated

    async def delete(self, category_id: int) -> CategoryModel:
        """Логическое удаление категории."""
        async with self._uow_factory() as uow:
            await self._get_active(uow, category_id)

            children = await uow.categories.get_active_children(category_id)
            if children:
                raise BusinessRuleError(
                    "Cannot delete category with children. Delete children first."
                )

            deleted = await uow.categories.delete_logical(category_id)
            if not deleted:
                raise NotFoundError("Category not found after delete")

            await uow.commit()
        return deleted

    async def get_root_categories(self) -> list[CategoryModel]:
        """Получить все корневые категории (без родителя)."""
        async with self._uow_factory() as uow:
            return await uow.categories.get_root_categories()

    async def get_category_tree(self, category_id: int | None = None) -> dict:
        """Получить дерево категорий (все узлы читаются в одной сессии)."""
        async with self._uow_factory() as uow:
            return await self._build_tree(uow, category_id)

    # ========== Внутренние помощники ==========

    @staticmethod
    async def _get_active(uow: AbstractUnitOfWork, category_id: int) -> CategoryModel:
        category = await uow.categories.get_active_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")
        return category

    async def _build_tree(self, uow: AbstractUnitOfWork, category_id: int | None) -> dict:
        if category_id:
            category = await self._get_active(uow, category_id)
            children = await uow.categories.get_active_children(category_id)
        else:
            category = None
            children = await uow.categories.get_root_categories()

        return {
            "category": category,
            "children": [await self._build_tree(uow, child.id) for child in children],
        }

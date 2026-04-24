from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.security import get_current_admin
from src.models import UserModel
from src.schemas import CategoryCreate, CategorySchema, CategoryTree
from src.service.categories import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """Возвращает список всех активных категорий."""
    return await CategoryService(db).get_all()


@router.get("/root", response_model=list[CategorySchema])
async def get_root_categories(db: AsyncSession = Depends(get_async_db)):
    """Возвращает список корневых категорий (без родителя)."""
    return await CategoryService(db).get_root_categories()


@router.get("/tree", response_model=CategoryTree)
async def get_category_tree(db: AsyncSession = Depends(get_async_db)):
    """Возвращает дерево категорий."""
    return await CategoryService(db).get_category_tree()


@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """Возвращает категорию по ID."""
    return await CategoryService(db).get_by_id(category_id)


@router.get("/{category_id}/tree", response_model=CategoryTree)
async def get_subcategory_tree(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """Возвращает дерево подкатегорий для указанной категории."""
    return await CategoryService(db).get_category_tree(category_id)


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: UserModel = Depends(get_current_admin),
):
    """Создаёт новую категорию. Только для администраторов."""
    return await CategoryService(db).create(category)


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: UserModel = Depends(get_current_admin),
):
    """Обновляет категорию по её ID."""
    return await CategoryService(db).update(category_id, category)


@router.delete("/{category_id}", response_model=CategorySchema, status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: UserModel = Depends(get_current_admin),
):
    """Удаляет категорию по её ID. Только для администраторов. Нельзя удалить категорию с дочерними."""
    return await CategoryService(db).delete(category_id)
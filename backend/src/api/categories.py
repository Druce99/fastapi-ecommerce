from fastapi import APIRouter, status
from src.api.dependencies import CategoryServiceDep, CurrentAdmin
from src.schemas import CategoryCreate, CategorySchema, CategoryTree

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(service: CategoryServiceDep):
    """Возвращает список всех активных категорий."""
    return await service.get_all()


@router.get("/root", response_model=list[CategorySchema])
async def get_root_categories(service: CategoryServiceDep):
    """Возвращает список корневых категорий (без родителя)."""
    return await service.get_root_categories()


@router.get("/tree", response_model=CategoryTree)
async def get_category_tree(service: CategoryServiceDep):
    """Возвращает дерево категорий."""
    return await service.get_category_tree()


@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(category_id: int, service: CategoryServiceDep):
    """Возвращает категорию по ID."""
    return await service.get_by_id(category_id)


@router.get("/{category_id}/tree", response_model=CategoryTree)
async def get_subcategory_tree(category_id: int, service: CategoryServiceDep):
    """Возвращает дерево подкатегорий для указанной категории."""
    return await service.get_category_tree(category_id)


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate, service: CategoryServiceDep, current_admin: CurrentAdmin
):
    """Создаёт новую категорию. Только для администраторов."""
    return await service.create(category)


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    service: CategoryServiceDep,
    current_admin: CurrentAdmin,
):
    """Обновляет категорию по её ID."""
    return await service.update(category_id, category)


@router.delete("/{category_id}", response_model=CategorySchema, status_code=status.HTTP_200_OK)
async def delete_category(
    category_id: int, service: CategoryServiceDep, current_admin: CurrentAdmin
):
    """Удаляет категорию по её ID. Только для администраторов. Нельзя удалить категорию с дочерними."""
    return await service.delete(category_id)

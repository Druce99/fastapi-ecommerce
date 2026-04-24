from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.security import get_current_seller
from src.models import UserModel
from src.schemas import ProductCreate, ProductList, ProductSchema, ReviewSchema
from src.service.products import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductList)
async def get_all_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, description="Поиск по названию товара"),
    category_id: int | None = Query(None, description="ID категории для фильтрации"),
    min_price: Decimal | None = Query(None, ge=0, description="Минимальная цена товара"),
    max_price: Decimal | None = Query(None, ge=0, description="Максимальная цена товара"),
    in_stock: bool | None = Query(None, description="true — только товары в наличии"),
    seller_id: int | None = Query(None, description="ID продавца для фильтрации"),
    created_after: datetime | None = Query(None, description="Товары, созданные после этой даты"),
    created_before: datetime | None = Query(None, description="Товары, созданные до этой даты"),
    db: AsyncSession = Depends(get_async_db),
):
    service = ProductService(db)
    return await service.get_all(
        page=page, page_size=page_size, search=search, category_id=category_id,
        min_price=min_price, max_price=max_price, in_stock=in_stock,
        seller_id=seller_id, created_after=created_after, created_before=created_before,
    )


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    return await ProductService(db).get_by_category(category_id)


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    return await ProductService(db).get_by_id(product_id)


@router.get("/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    return await ProductService(db).get_reviews(product_id)


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate = Depends(ProductCreate.as_form),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    return await ProductService(db).create(product, current_user, image)


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductCreate = Depends(ProductCreate.as_form),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    return await ProductService(db).update(product_id, product, current_user, image)


@router.delete("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    return await ProductService(db).delete(product_id, current_user)

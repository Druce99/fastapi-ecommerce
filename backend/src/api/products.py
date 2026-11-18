from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from src.api.dependencies import CurrentSeller, ProductServiceDep
from src.schemas import ProductCreate, ProductList, ProductSchema, ReviewSchema

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=ProductList)
async def get_all_products(
    service: ProductServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[
        str | None, Query(min_length=1, description="Поиск по названию товара")
    ] = None,
    category_id: Annotated[int | None, Query(description="ID категории для фильтрации")] = None,
    min_price: Annotated[Decimal | None, Query(ge=0, description="Минимальная цена товара")] = None,
    max_price: Annotated[
        Decimal | None, Query(ge=0, description="Максимальная цена товара")
    ] = None,
    in_stock: Annotated[bool | None, Query(description="true — только товары в наличии")] = None,
    seller_id: Annotated[int | None, Query(description="ID продавца для фильтрации")] = None,
    created_after: Annotated[
        datetime | None, Query(description="Товары, созданные после этой даты")
    ] = None,
    created_before: Annotated[
        datetime | None, Query(description="Товары, созданные до этой даты")
    ] = None,
):
    return await service.get_all(
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        seller_id=seller_id,
        created_after=created_after,
        created_before=created_before,
    )


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, service: ProductServiceDep):
    return await service.get_by_category(category_id)


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, service: ProductServiceDep):
    return await service.get_by_id(product_id)


@router.get("/{product_id}/reviews", response_model=list[ReviewSchema])
async def get_product_reviews(product_id: int, service: ProductServiceDep):
    return await service.get_reviews(product_id)


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: Annotated[ProductCreate, Depends(ProductCreate.as_form)],
    service: ProductServiceDep,
    current_user: CurrentSeller,
    image: Annotated[UploadFile | None, File()] = None,
):
    return await service.create(product, current_user, image)


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: Annotated[ProductCreate, Depends(ProductCreate.as_form)],
    service: ProductServiceDep,
    current_user: CurrentSeller,
    image: Annotated[UploadFile | None, File()] = None,
):
    return await service.update(product_id, product, current_user, image)


@router.delete("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, service: ProductServiceDep, current_user: CurrentSeller):
    return await service.delete(product_id, current_user)

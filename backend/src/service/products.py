from datetime import datetime
from decimal import Decimal

from fastapi import UploadFile
from src.core.exceptions import BusinessRuleError, NotFoundError, PermissionDeniedError
from src.core.images import remove_product_image, save_product_image
from src.models import ProductModel, ReviewModel, UserModel
from src.repository.uow import UnitOfWorkFactory
from src.schemas import ProductCreate


class ProductService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_all(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        seller_id: int | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> dict:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise BusinessRuleError("min_price не может быть больше max_price")
        if (
            created_after is not None
            and created_before is not None
            and created_after > created_before
        ):
            raise BusinessRuleError("created_after не может быть позже created_before")

        async with self._uow_factory() as uow:
            items, total = await uow.products.get_filtered(
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
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_by_id(self, product_id: int) -> ProductModel:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found or inactive")
        return product

    async def get_by_category(self, category_id: int) -> list[ProductModel]:
        async with self._uow_factory() as uow:
            category = await uow.categories.get_active_by_id(category_id)
            if not category:
                raise NotFoundError("Category not found or inactive")
            return await uow.products.get_by_category(category_id)

    async def get_reviews(self, product_id: int) -> list[ReviewModel]:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(product_id)
            if not product:
                raise NotFoundError("Product not found")
            return await uow.reviews.get_by_product(product_id)

    async def create(
        self, product_data: ProductCreate, current_user: UserModel, image: UploadFile | None = None
    ) -> ProductModel:
        async with self._uow_factory() as uow:
            category = await uow.categories.get_active_by_id(product_data.category_id)
            if not category:
                raise BusinessRuleError("Category not found or inactive")
            image_url = await save_product_image(image) if image else None
            product = await uow.products.create(
                **product_data.model_dump(), seller_id=current_user.id, image_url=image_url
            )
            await uow.commit()
        return product

    async def update(
        self,
        product_id: int,
        product_data: ProductCreate,
        current_user: UserModel,
        image: UploadFile | None = None,
    ) -> ProductModel:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(product_id)
            if not product:
                raise NotFoundError("Product not found")
            if product.seller_id != current_user.id:
                raise PermissionDeniedError("You can only update your own products")
            category = await uow.categories.get_active_by_id(product_data.category_id)
            if not category:
                raise BusinessRuleError("Category not found or inactive")
            image_url = product.image_url
            if image:
                remove_product_image(product.image_url)
                image_url = await save_product_image(image)
            updated = await uow.products.update(
                product_id, {**product_data.model_dump(), "image_url": image_url}
            )
            await uow.commit()
        return updated

    async def delete(self, product_id: int, current_user: UserModel) -> ProductModel:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(product_id)
            if not product:
                raise NotFoundError("Product not found or inactive")
            if product.seller_id != current_user.id:
                raise PermissionDeniedError("You can only delete your own products")
            deleted = await uow.products.delete_logical(product_id)
            await uow.commit()
        return deleted

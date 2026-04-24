from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ProductModel, ReviewModel, UserModel
from src.repository.categories import CategoryRepository
from src.repository.products import ProductRepository
from src.schemas import ProductCreate
from src.core.images import remove_product_image, save_product_image


class ProductService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.db = db

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_price не может быть больше max_price",
            )
        if created_after is not None and created_before is not None and created_after > created_before:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="created_after не может быть позже created_before",
            )

        items, total = await self.repo.get_filtered(
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
        product = await self.repo.get_active_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inactive",
            )
        return product

    async def get_by_category(self, category_id: int) -> list[ProductModel]:
        category = await self.category_repo.get_active_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive",
            )
        return await self.repo.get_by_category(category_id)

    async def get_reviews(self, product_id: int) -> list[ReviewModel]:
        product = await self.repo.get_active_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return await self.repo.get_active_reviews(product_id)

    async def create(self, product_data: ProductCreate, current_user: UserModel, image: UploadFile | None = None) -> ProductModel:
        category = await self.category_repo.get_active_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or inactive",
            )
        image_url = await save_product_image(image) if image else None
        product = await self.repo.create(**product_data.model_dump(), seller_id=current_user.id, image_url=image_url)
        await self.db.commit()
        return product

    async def update(self, product_id: int, product_data: ProductCreate, current_user: UserModel,image: UploadFile | None = None) -> ProductModel:
        product = await self.repo.get_active_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if product.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own products",
            )
        category = await self.category_repo.get_active_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or inactive",
            )
        image_url = product.image_url
        if image:
            remove_product_image(product.image_url)
            image_url = await save_product_image(image)
        updated = await self.repo.update(product_id, {**product_data.model_dump(),"image_url": image_url})
        await self.db.commit()
        return updated

    async def delete(self, product_id: int, current_user: UserModel) -> ProductModel:
        product = await self.repo.get_active_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inactive",
            )
        if product.seller_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own products",
            )
        deleted = await self.repo.delete_logical(product_id)
        await self.db.commit()
        return deleted

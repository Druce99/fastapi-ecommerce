from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ProductModel, ReviewModel
from src.repository.base import BaseRepository


class ReviewRepository(BaseRepository[ReviewModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ReviewModel, db)

    async def get_all_reviews(self) -> list[ReviewModel]:
        result = await self.db.scalars(
            select(self.model).where(self.model.is_active == True)
        )
        return result.all()

    async def get_by_product(self, product_id: int) -> list[ReviewModel]:
        result = await self.db.scalars(
            select(self.model).where(
                self.model.product_id == product_id,
                self.model.is_active == True,
            )
        )
        return result.all()

    async def get_by_user_and_product(self, user_id: int, product_id: int) -> ReviewModel | None:
        result = await self.db.scalars(
            select(self.model).where(
                self.model.user_id == user_id,
                self.model.product_id == product_id,
                self.model.is_active == True,
            )
        )
        return result.first()

    async def update_product_rating(self, product_id: int) -> None:
        avg_rating = await self.db.scalar(
            select(func.avg(self.model.grade)).where(
                self.model.product_id == product_id,
                self.model.is_active == True,
            )
        )
        product = await self.db.get(ProductModel, product_id)
        if product:
            product.rating = avg_rating or 0.00
            await self.db.flush()

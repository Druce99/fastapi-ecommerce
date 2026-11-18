from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import ReviewModel
from src.repository.base import BaseRepository


class ReviewRepository(BaseRepository[ReviewModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ReviewModel, db)

    async def get_all_reviews(self) -> list[ReviewModel]:
        result = await self.db.scalars(select(self.model).where(self.model.is_active.is_(True)))
        return list(result.all())

    async def get_by_product(self, product_id: int) -> list[ReviewModel]:
        result = await self.db.scalars(
            select(self.model).where(
                self.model.product_id == product_id,
                self.model.is_active.is_(True),
            )
        )
        return list(result.all())

    async def get_by_user_and_product(self, user_id: int, product_id: int) -> ReviewModel | None:
        result = await self.db.scalars(
            select(self.model).where(
                self.model.user_id == user_id,
                self.model.product_id == product_id,
                self.model.is_active.is_(True),
            )
        )
        return result.first()

    async def get_average_grade(self, product_id: int) -> Decimal:
        """Средняя оценка активных отзывов товара (0, если отзывов нет)."""
        avg_rating = await self.db.scalar(
            select(func.avg(self.model.grade)).where(
                self.model.product_id == product_id,
                self.model.is_active.is_(True),
            )
        )
        return Decimal(avg_rating or 0)

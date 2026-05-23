from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ProductModel, ReviewModel
from src.repository.base import BaseRepository


class ProductRepository(BaseRepository[ProductModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ProductModel, db)

    async def get_by_category(self, category_id: int) -> list[ProductModel]:
        result = await self.db.scalars(
            select(self.model).where(
                self.model.category_id == category_id,
                self.model.is_active == True,
            )
        )
        return result.all()

    async def get_active_reviews(self, product_id: int) -> list[ReviewModel]:
        result = await self.db.scalars(
            select(ReviewModel).where(
                ReviewModel.product_id == product_id,
                ReviewModel.is_active == True,
            )
        )
        return result.all()

    async def get_filtered(
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
    ) -> tuple[list[ProductModel], int]:
        filters = [self.model.is_active.is_(True)]

        if category_id is not None:
            filters.append(self.model.category_id == category_id)
        if min_price is not None:
            filters.append(self.model.price >= min_price)
        if max_price is not None:
            filters.append(self.model.price <= max_price)
        if in_stock is not None:
            filters.append(self.model.stock > 0 if in_stock else self.model.stock == 0)
        if seller_id is not None:
            filters.append(self.model.seller_id == seller_id)
        if created_after is not None:
            filters.append(self.model.created_at >= created_after)
        if created_before is not None:
            filters.append(self.model.created_at <= created_before)

        rank_col = None
        if search:
            ts_query = func.websearch_to_tsquery("english", search.strip())
            filters.append(self.model.tsv.op("@@")(ts_query))
            rank_col = func.ts_rank_cd(self.model.tsv, ts_query).label("rank")

        total = await self.db.scalar(
            select(func.count()).select_from(self.model).where(*filters)
        ) or 0

        offset = (page - 1) * page_size
        if rank_col is not None:
            stmt = (
                select(self.model, rank_col)
                .where(*filters)
                .order_by(desc(rank_col), self.model.id)
                .offset(offset)
                .limit(page_size)
            )
            result = await self.db.execute(stmt)
            items = [row[0] for row in result.all()]
        else:
            stmt = (
                select(self.model)
                .where(*filters)
                .order_by(self.model.id)
                .offset(offset)
                .limit(page_size)
            )
            items = (await self.db.scalars(stmt)).all()

        return items, total

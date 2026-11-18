from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models import OrderItemModel, OrderModel

from .base import BaseRepository


class OrderRepository(BaseRepository[OrderModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(OrderModel, db)

    async def get_by_id_with_items(self, order_id: int, *, lock: bool = False) -> OrderModel | None:
        """Заказ с позициями. lock=True блокирует строку заказа (SELECT ... FOR UPDATE)."""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
            .where(OrderModel.id == order_id)
        )
        if lock:
            stmt = stmt.with_for_update(of=OrderModel)
        result = await self.db.scalars(stmt)
        return result.first()

    async def get_user_orders(self, user_id: int, offset: int, limit: int) -> list[OrderModel]:
        result = await self.db.scalars(
            select(OrderModel)
            .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def count_user_orders(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(OrderModel.id)).where(OrderModel.user_id == user_id)
        )
        return result.scalar_one()

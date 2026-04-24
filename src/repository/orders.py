from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import OrderModel, OrderItemModel
from .base import BaseRepository

class OrderRepository(BaseRepository[OrderModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(OrderModel, db)
    
    async def get_by_id_with_items(self, order_id: int) -> OrderModel | None:
        result = await self.db.scalars(
            select(OrderModel)
            .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
            .where(OrderModel.id == order_id)
        )
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
        return result.all()
    
    async def count_user_orders(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(OrderModel.id)).where(OrderModel.user_id == user_id)
        )
        return result.scalar_one()
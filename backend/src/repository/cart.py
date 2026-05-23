from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import CartItemModel

from .base import BaseRepository


class CartRepository(BaseRepository[CartItemModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(CartItemModel, db)

    async def get_cart_items(self, user_id: int) -> list[CartItemModel]:
        """Получить содержимое корзины."""
        result = await self.db.scalars(
            select(CartItemModel)
            .options(selectinload(CartItemModel.product))
            .where(CartItemModel.user_id == user_id)
            .order_by(CartItemModel.id)
        )
        return result.all()

    async def get_cart_item(self, user_id: int, product_id: int) -> CartItemModel | None:
        """Получить позицию корзины по пользователю и товару."""
        result = await self.db.scalars(
            select(CartItemModel)
            .options(selectinload(CartItemModel.product))
            .where(
                CartItemModel.user_id == user_id,
                CartItemModel.product_id == product_id,
            )
        )
        return result.first()

    async def clear_cart(self, user_id: int) -> None:
        """Очистить корзину пользователя."""
        await self.db.execute(delete(CartItemModel).where(CartItemModel.user_id == user_id))

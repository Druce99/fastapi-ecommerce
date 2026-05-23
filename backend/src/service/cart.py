from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.cart import CartRepository
from src.repository.products import ProductRepository
from src.schemas import CartItemCreate, CartItemSchema, CartItemUpdate, CartSchema


class CartService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CartRepository(db=db)
        self.product_repo = ProductRepository(db=db)
        self.db = db

    async def get_cart(self, user_id: int) -> CartSchema:
        items = await self.repo.get_cart_items(user_id=user_id)
        total_quantity = sum(item.quantity for item in items)
        price_items = (
            Decimal(item.quantity) *
            (item.product.price if item.product.price is not None else Decimal("0"))
            for item in items
        )
        total_price = sum(price_items, Decimal("0.00"))

        return CartSchema(
            user_id=user_id,
            items=items,
            total_quantity=total_quantity,
            total_price=total_price,
        )

    async def add_item(self, user_id: int, payload: CartItemCreate) -> CartItemSchema:
        product = await self.product_repo.get_active_by_id(id=payload.product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        item = await self.repo.get_cart_item(user_id=user_id, product_id=payload.product_id)
        if item:
            await self.repo.update(item.id, {"quantity": item.quantity + payload.quantity})
        else:
            await self.repo.create(user_id=user_id, **payload.model_dump())

        await self.db.commit()

        updated_item = await self.repo.get_cart_item(user_id=user_id, product_id=payload.product_id)
        return updated_item

    async def update_item(self, user_id: int, product_id: int, payload: CartItemUpdate) -> CartItemSchema:
        product = await self.product_repo.get_active_by_id(id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        item = await self.repo.get_cart_item(user_id=user_id, product_id=product_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in cart")

        await self.repo.update(id=item.id, update_data={"quantity": payload.quantity})
        await self.db.commit()

        item = await self.repo.get_cart_item(user_id=user_id, product_id=product_id)
        return item

    async def remove_item(self, user_id: int, product_id: int) -> None:
        item = await self.repo.get_cart_item(user_id=user_id, product_id=product_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in cart")
        await self.repo.delete_physical(id=item.id)
        await self.db.commit()

    async def clear_cart(self, user_id: int) -> None:
        await self.repo.clear_cart(user_id=user_id)
        await self.db.commit()
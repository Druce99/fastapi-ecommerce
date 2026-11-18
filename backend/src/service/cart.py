from decimal import Decimal

from src.core.exceptions import NotFoundError
from src.models import CartItemModel
from src.repository.uow import UnitOfWorkFactory
from src.schemas import CartItemCreate, CartItemUpdate, CartSchema


class CartService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_cart(self, user_id: int) -> CartSchema:
        async with self._uow_factory() as uow:
            items = await uow.cart.get_cart_items(user_id=user_id)

        total_quantity = sum(item.quantity for item in items)
        price_items = (
            Decimal(item.quantity)
            * (item.product.price if item.product.price is not None else Decimal("0"))
            for item in items
        )
        total_price = sum(price_items, Decimal("0.00"))

        return CartSchema(
            user_id=user_id,
            items=items,
            total_quantity=total_quantity,
            total_price=total_price,
        )

    async def add_item(self, user_id: int, payload: CartItemCreate) -> CartItemModel:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(id=payload.product_id)
            if product is None:
                raise NotFoundError("Product not found")

            item = await uow.cart.get_cart_item(user_id=user_id, product_id=payload.product_id)
            if item:
                await uow.cart.update(item.id, {"quantity": item.quantity + payload.quantity})
            else:
                await uow.cart.create(user_id=user_id, **payload.model_dump())
            await uow.commit()

            updated_item = await uow.cart.get_cart_item(
                user_id=user_id, product_id=payload.product_id
            )
        return updated_item

    async def update_item(
        self, user_id: int, product_id: int, payload: CartItemUpdate
    ) -> CartItemModel:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(id=product_id)
            if product is None:
                raise NotFoundError("Product not found")

            item = await uow.cart.get_cart_item(user_id=user_id, product_id=product_id)
            if item is None:
                raise NotFoundError("Product not found in cart")

            await uow.cart.update(id=item.id, update_data={"quantity": payload.quantity})
            await uow.commit()

            updated_item = await uow.cart.get_cart_item(user_id=user_id, product_id=product_id)
        return updated_item

    async def remove_item(self, user_id: int, product_id: int) -> None:
        async with self._uow_factory() as uow:
            item = await uow.cart.get_cart_item(user_id=user_id, product_id=product_id)
            if item is None:
                raise NotFoundError("Product not found in cart")
            await uow.cart.delete_physical(id=item.id)
            await uow.commit()

    async def clear_cart(self, user_id: int) -> None:
        async with self._uow_factory() as uow:
            await uow.cart.clear_cart(user_id=user_id)
            await uow.commit()

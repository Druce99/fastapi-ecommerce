from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.cart import CartRepository
from src.repository.products import ProductRepository
from src.repository.orders import OrderRepository
from src.models import OrderModel, OrderItemModel
from src.schemas import OrderSchema, OrderListSchema, OrderCreatedSchema
from src.core.broker import broker
from src.service.payments import create_yookassa_payment
from src.schemas.orders import OrderCheckoutResponse

class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.db = db
    
    async def checkout(self, user_id: int, email: str) -> OrderCheckoutResponse:
        # 1. Проверяем корзину
        cart_items = await self.cart_repo.get_cart_items(user_id=user_id)
        if not cart_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
        
        # 2. Блокируем товары от гонки (SELECT FOR UPDATE)
        product_ids = [item.product_id for item in cart_items]
        products = await ProductRepository(self.db).get_by_ids_for_update(product_ids)
        product_map = {p.id: p for p in products}
        
        # 3. Создаём заказ и считаем сумму
        order = OrderModel(user_id=user_id)
        total_amount = Decimal("0")
        
        for cart_item in cart_items:
            product = product_map.get(cart_item.product_id)
            if not product or not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {cart_item.product_id} is unavailable")
            if product.stock < cart_item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for product {product.name}")
            
            unit_price = product.price
            total_price = unit_price * cart_item.quantity
            total_amount += total_price
            order.items.append(OrderItemModel(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=unit_price,
                total_price=total_price,
            ))
            product.stock -= cart_item.quantity
        order.total_amount = total_amount
        await self.repo.add(order)
        # 4. flush() — сохраняет в БД без коммита, чтобы получить order.id
        await self.db.flush()
        # 5. Создаём платёж в ЮKassa
        try:
            payment_info = await create_yookassa_payment(
                order_id=order.id,
                amount=total_amount,
                user_email=email,
                description=f"Заказ №{order.id} в DruceShop",
            )
        except RuntimeError as exc:
            # Наша ошибка — неправильные настройки
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        except Exception as exc:
            # Внешняя ошибка — ЮKassa недоступна
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        
        # 6. Сохраняем payment_id и очищаем корзину
        order.payment_id = payment_info.get("id")
        await self.cart_repo.clear_cart(user_id=user_id)
        await self.db.commit()
        # 7. Загружаем заказ с позициями для ответа
        created_order = await self.repo.get_by_id_with_items(order_id=order.id)
        # 8. Уведомление
        await broker.publish(
            OrderCreatedSchema(order_id=created_order.id, email=email),
            channel="order_created",
        )
        return OrderCheckoutResponse(
            order = created_order,
            confirmation_url = payment_info.get("confirmation_url"),
        )
    
    async def get_order(self, user_id: int, order_id: int) -> OrderModel:
        order = await self.repo.get_by_id_with_items(order_id=order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order
    
    async def list_orders(self, user_id: int, page: int, page_size: int) -> OrderListSchema:
        total = await self.repo.count_user_orders(user_id=user_id)
        orders = await self.repo.get_user_orders(
            user_id=user_id,
            offset=(page-1) * page_size,
            limit=page_size
        )
        return OrderListSchema(items=orders, total=total, page=page, page_size=page_size)
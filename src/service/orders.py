from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository.cart import CartRepository
from src.repository.orders import OrderRepository
from src.models import OrderModel, OrderItemModel
from src.schemas import OrderSchema, OrderListSchema, OrderCreatedSchema
from src.core.broker import broker

class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.db = db
    
    async def checkout(self, user_id: int, email: str) -> OrderModel:
        cart_items = await self.cart_repo.get_cart_items(user_id=user_id)
        if not cart_items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
        order = OrderModel(user_id=user_id)
        total_amount = Decimal("0")
        
        for cart_item in cart_items:
            product = cart_item.product
            if not product or not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product {cart_item.product_id} is unavailable")
            if product.stock < cart_item.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for product {product.name}")
            
            unit_price = product.price
            total_price = unit_price * cart_item.quantity
            total_amount += total_price
            
            order.items.append(OrderItemModel(
                product_id = cart_item.product_id,
                quantity = cart_item.quantity,
                unit_price = unit_price,
                total_price = total_price
            ))
            product.stock -= cart_item.quantity
        
        order.total_amount = total_amount
        await self.repo.add(order)
        await self.cart_repo.clear_cart(user_id=user_id)
        await self.db.commit()
        
        created_order = await self.repo.get_by_id_with_items(order.id)
        
        await broker.publish(
            OrderCreatedSchema(order_id=created_order.id, email=email),
            channel="order_created"
        )
        
        return created_order
    
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
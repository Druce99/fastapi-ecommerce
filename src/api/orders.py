from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.security import get_current_user
from src.models import UserModel
from src.schemas import OrderSchema, OrderListSchema
from src.service.orders import OrderService

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

@router.post("/checkout", response_model=OrderSchema, status_code=status.HTTP_201_CREATED)
async def checkout_order(db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await OrderService(db).checkout(current_user.id)

@router.get("/",response_model=OrderListSchema)
async def list_orders(page: int = Query(1,ge=1), page_size: int = Query(10, ge=1, le=100), db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await OrderService(db).list_orders(current_user.id, page=page, page_size=page_size)

@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(order_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await OrderService(db).get_order(current_user.id, order_id)
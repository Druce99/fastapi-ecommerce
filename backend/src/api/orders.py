from typing import Annotated

from fastapi import APIRouter, Query, status
from src.api.dependencies import CurrentUser, OrderServiceDep
from src.schemas import OrderListSchema, OrderSchema
from src.schemas.orders import OrderCheckoutResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderCheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout_order(service: OrderServiceDep, current_user: CurrentUser):
    return await service.checkout(current_user.id, current_user.email)


@router.get("/", response_model=OrderListSchema)
async def list_orders(
    service: OrderServiceDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.list_orders(current_user.id, page=page, page_size=page_size)


@router.get("/{order_id}", response_model=OrderSchema)
async def get_order(order_id: int, service: OrderServiceDep, current_user: CurrentUser):
    return await service.get_order(current_user.id, order_id)

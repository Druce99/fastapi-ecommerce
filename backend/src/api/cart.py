from fastapi import APIRouter, status
from src.api.dependencies import CartServiceDep, CurrentUser
from src.schemas import CartItemCreate, CartItemSchema, CartItemUpdate, CartSchema

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartSchema, status_code=status.HTTP_200_OK)
async def get_cart(service: CartServiceDep, current_user: CurrentUser):
    return await service.get_cart(current_user.id)


@router.post("/items", response_model=CartItemSchema, status_code=status.HTTP_201_CREATED)
async def add_item(payload: CartItemCreate, service: CartServiceDep, current_user: CurrentUser):
    return await service.add_item(current_user.id, payload)


@router.put("/items/{product_id}", response_model=CartItemSchema, status_code=status.HTTP_200_OK)
async def update_item(
    product_id: int,
    payload: CartItemUpdate,
    service: CartServiceDep,
    current_user: CurrentUser,
):
    return await service.update_item(current_user.id, product_id, payload)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(product_id: int, service: CartServiceDep, current_user: CurrentUser):
    return await service.remove_item(current_user.id, product_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(service: CartServiceDep, current_user: CurrentUser):
    return await service.clear_cart(current_user.id)

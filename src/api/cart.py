from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.security import get_current_user
from src.models import UserModel
from src.schemas import CartSchema, CartItemSchema, CartItemCreate, CartItemUpdate
from src.service.cart import CartService

router = APIRouter(
    prefix="/cart",
    tags=["cart"]
)

@router.get("/", response_model=CartSchema, status_code=status.HTTP_200_OK)
async def get_cart(db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await CartService(db).get_cart(current_user.id)

@router.post("/items", response_model=CartItemSchema, status_code=status.HTTP_201_CREATED)
async def add_item(payload: CartItemCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await CartService(db).add_item(current_user.id, payload)

@router.put("/items/{product_id}", response_model=CartItemSchema, status_code=status.HTTP_200_OK)
async def update_item(product_id: int, payload: CartItemUpdate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await CartService(db).update_item(current_user.id,product_id, payload)

@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(product_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await CartService(db).remove_item(current_user.id, product_id)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    return await CartService(db).clear_cart(current_user.id)
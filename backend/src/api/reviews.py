from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.core.security import get_current_buyer, get_current_user
from src.models import UserModel
from src.schemas import CreateReview, ReviewSchema
from src.service.reviews import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    return await ReviewService(db).get_all()


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: CreateReview,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer),
):
    return await ReviewService(db).create(review, current_user)


@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    return await ReviewService(db).delete(review_id, current_user)

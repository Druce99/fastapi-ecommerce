from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ReviewModel, UserModel
from src.repository.products import ProductRepository
from src.repository.reviews import ReviewRepository
from src.schemas import CreateReview


class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = ReviewRepository(db)
        self.product_repo = ProductRepository(db)
        self.db = db

    async def get_all(self) -> list[ReviewModel]:
        return await self.repo.get_all_reviews()

    async def create(self, review_data: CreateReview, current_user: UserModel) -> ReviewModel:
        product = await self.product_repo.get_active_by_id(review_data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        existing = await self.repo.get_by_user_and_product(current_user.id, review_data.product_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this product",
            )

        review = await self.repo.create(**review_data.model_dump(), user_id=current_user.id)
        await self.repo.update_product_rating(product.id)
        await self.db.commit()
        return review

    async def delete(self, review_id: int, current_user: UserModel) -> dict:
        review = await self.repo.get_active_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )
        if current_user.id != review.user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own reviews",
            )

        product_id = review.product_id
        await self.repo.delete_logical(review_id)
        await self.repo.update_product_rating(product_id)
        await self.db.commit()
        return {"message": "Review deleted successfully"}

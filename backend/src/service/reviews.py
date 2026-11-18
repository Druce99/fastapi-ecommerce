from src.core.exceptions import BusinessRuleError, NotFoundError, PermissionDeniedError
from src.models import ReviewModel, UserModel
from src.repository.uow import AbstractUnitOfWork, UnitOfWorkFactory
from src.schemas import CreateReview


class ReviewService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def get_all(self) -> list[ReviewModel]:
        async with self._uow_factory() as uow:
            return await uow.reviews.get_all_reviews()

    async def create(self, review_data: CreateReview, current_user: UserModel) -> ReviewModel:
        async with self._uow_factory() as uow:
            product = await uow.products.get_active_by_id(review_data.product_id)
            if not product:
                raise NotFoundError("Product not found")

            existing = await uow.reviews.get_by_user_and_product(
                current_user.id, review_data.product_id
            )
            if existing:
                raise BusinessRuleError("You have already reviewed this product")

            review = await uow.reviews.create(**review_data.model_dump(), user_id=current_user.id)
            await self._refresh_product_rating(uow, product.id)
            await uow.commit()
        return review

    async def delete(self, review_id: int, current_user: UserModel) -> dict:
        async with self._uow_factory() as uow:
            review = await uow.reviews.get_active_by_id(review_id)
            if not review:
                raise NotFoundError("Review not found")
            if current_user.id != review.user_id and current_user.role != "admin":
                raise PermissionDeniedError("You can only delete your own reviews")

            product_id = review.product_id
            await uow.reviews.delete_logical(review_id)
            await self._refresh_product_rating(uow, product_id)
            await uow.commit()
        return {"message": "Review deleted successfully"}

    @staticmethod
    async def _refresh_product_rating(uow: AbstractUnitOfWork, product_id: int) -> None:
        """Пересчитать рейтинг товара по активным отзывам (в текущей транзакции)."""
        average = await uow.reviews.get_average_grade(product_id)
        await uow.products.set_rating(product_id, average)

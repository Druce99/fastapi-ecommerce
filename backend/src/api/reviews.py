from fastapi import APIRouter, status
from src.api.dependencies import CurrentBuyer, CurrentUser, ReviewServiceDep
from src.schemas import CreateReview, ReviewSchema

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_all_reviews(service: ReviewServiceDep):
    return await service.get_all()


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: CreateReview, service: ReviewServiceDep, current_user: CurrentBuyer
):
    return await service.create(review, current_user)


@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(review_id: int, service: ReviewServiceDep, current_user: CurrentUser):
    return await service.delete(review_id, current_user)

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateReview(BaseModel):
    product_id: int = Field(..., description="ID товара")
    comment: str | None = Field(None, description="Комментарий")
    grade: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")


class Review(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор отзыва")
    user_id: int = Field(..., description="ID пользователя")
    product_id: int = Field(..., description="ID товара")
    comment: str | None = Field(None, description="Комментарий")
    comment_date: datetime = Field(..., description="Дата комментария")
    grade: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")
    is_active: bool = Field(..., description="Активность")

    model_config = ConfigDict(from_attributes=True)
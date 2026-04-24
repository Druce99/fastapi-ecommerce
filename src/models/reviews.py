from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    comment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __str__(self) -> str:
        return f"Review #{self.id} (grade: {self.grade})"

    user: Mapped["User"] = relationship(
        "User",
        back_populates="reviews",
    )
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="reviews",
    )
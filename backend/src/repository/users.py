from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import UserModel
from src.repository.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(UserModel, db)

    async def get_by_email(self, email: str) -> UserModel | None:
        """Получить пользователя по email."""
        result = await self.db.scalars(select(self.model).where(self.model.email == email))
        return result.first()

    async def get_active_by_email(self, email: str) -> UserModel | None:
        """Получить активного пользователя по email."""
        result = await self.db.scalars(
            select(self.model).where(
                self.model.email == email,
                self.model.is_active.is_(True),
            )
        )
        return result.first()

    async def update_role(self, user_id: int, role: str) -> UserModel | None:
        """Обновить роль пользователя."""
        return await self.update(user_id, {"role": role})

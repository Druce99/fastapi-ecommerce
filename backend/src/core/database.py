from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass

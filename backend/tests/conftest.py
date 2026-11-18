import os

os.environ.setdefault("BCRYPT_ROUNDS", "4")  # быстрые пароли в тестах (в проде 12)
os.environ.setdefault("DEBUG", "true")  # до импорта настроек: иначе валидатор потребует секреты

from functools import partial

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from src.api.dependencies import get_uow_factory
from src.core.config import settings
from src.core.database import Base
from src.core.security import hash_password
from src.main import app
from src.models import UserModel
from src.repository.uow import SqlAlchemyUnitOfWork, UnitOfWorkFactory

# Тестовая БД — отдельная от продакшн
TEST_DB_NAME = f"{settings.DB_NAME}_test"
ADMIN_DB_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
TEST_DB_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + f"/{TEST_DB_NAME}"

engine_test = create_async_engine(TEST_DB_URL, poolclass=NullPool, echo=False)
session_maker_test = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)


# ========== БД: создать таблицы один раз, удалить после всех тестов ==========


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    # Создаём тестовую БД, если её ещё нет (CREATE DATABASE нельзя в транзакции)
    admin_engine = create_async_engine(
        ADMIN_DB_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB_NAME}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))  # noqa: S608
    await admin_engine.dispose()

    async with engine_test.begin() as conn:
        # PostgreSQL 15+: схема public закрыта по умолчанию
        await conn.execute(text("GRANT ALL ON SCHEMA public TO CURRENT_USER"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ========== Admin: создаётся один раз на всю сессию ==========


@pytest_asyncio.fixture(scope="session")
async def admin_in_db(prepare_database):
    async with session_maker_test() as session:
        result = await session.scalars(select(UserModel).where(UserModel.email == "admin@test.com"))
        existing = result.first()
        if existing:
            return existing

        user = UserModel(
            email="admin@test.com",
            hashed_password=hash_password("admin123456"),
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# ========== Сессия БД и клиент для каждого теста ==========


def _test_uow_factory() -> UnitOfWorkFactory:
    """Каждый UoW в тестах работает с тестовой БД через собственную сессию."""
    return partial(SqlAlchemyUnitOfWork, session_maker_test)


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_uow_factory] = _test_uow_factory
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ========== Токены ==========


@pytest_asyncio.fixture
async def admin_token(client, admin_in_db):
    resp = await client.post(
        "/users/token",
        data={
            "username": "admin@test.com",
            "password": "admin123456",
        },
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def seller_token(client):
    import uuid

    email = f"seller_{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/users/",
        json={
            "email": email,
            "password": "seller123456",
            "role": "seller",
        },
    )
    resp = await client.post(
        "/users/token",
        data={
            "username": email,
            "password": "seller123456",
        },
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def buyer_token(client):
    import uuid

    email = f"buyer_{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        "/users/",
        json={
            "email": email,
            "password": "buyer123456",
            "role": "buyer",
        },
    )
    resp = await client.post(
        "/users/token",
        data={
            "username": email,
            "password": "buyer123456",
        },
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


# ========== Вспомогательные фикстуры ==========


@pytest_asyncio.fixture
async def category(client, admin_token):
    import uuid

    resp = await client.post(
        "/categories/",
        json={"name": f"Test Category {uuid.uuid4().hex[:6]}", "parent_id": None},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()


@pytest_asyncio.fixture
async def product(client, seller_token, category):
    resp = await client.post(
        "/products/",
        # Эндпоинт принимает form-data (вместе с полем image), а не JSON
        data={
            "name": "Test Product",
            "description": "Test description",
            "price": "99.99",
            "stock": 10,
            "category_id": category["id"],
        },
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()

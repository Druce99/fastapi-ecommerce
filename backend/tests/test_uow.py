"""Поведение Unit of Work: фиксация, откат при ошибке, отсутствие commit."""

import uuid

import pytest
from src.repository.uow import SqlAlchemyUnitOfWork

from tests.conftest import session_maker_test


def _email() -> str:
    return f"uow_{uuid.uuid4().hex[:8]}@test.com"


async def _exists(email: str) -> bool:
    async with SqlAlchemyUnitOfWork(session_maker_test) as uow:
        return await uow.users.get_by_email(email) is not None


async def test_commit_persists_changes():
    email = _email()
    async with SqlAlchemyUnitOfWork(session_maker_test) as uow:
        await uow.users.create(email=email, hashed_password="x", role="buyer")  # noqa: S106
        await uow.commit()

    assert await _exists(email)


async def test_exception_rolls_back_changes():
    email = _email()
    with pytest.raises(RuntimeError):
        async with SqlAlchemyUnitOfWork(session_maker_test) as uow:
            await uow.users.create(email=email, hashed_password="x", role="buyer")  # noqa: S106
            raise RuntimeError

    assert not await _exists(email)


async def test_changes_without_commit_are_discarded():
    email = _email()
    async with SqlAlchemyUnitOfWork(session_maker_test) as uow:
        await uow.users.create(email=email, hashed_password="x", role="buyer")  # noqa: S106

    assert not await _exists(email)


async def test_loaded_object_is_usable_after_uow_exit():
    email = _email()
    async with SqlAlchemyUnitOfWork(session_maker_test) as uow:
        user = await uow.users.create(email=email, hashed_password="x", role="buyer")  # noqa: S106
        await uow.commit()

    assert user.email == email
    assert user.id is not None

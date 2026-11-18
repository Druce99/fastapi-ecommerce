"""Соответствие «исключение приложения → HTTP-ответ». БД не нужна."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.api.error_handlers import register_error_handlers, resolve_status_code
from src.core.exceptions import (
    AlreadyExistsError,
    AppError,
    AuthenticationError,
    BusinessRuleError,
    ConfigurationError,
    EmailAlreadyRegisteredError,
    EmptyCartError,
    ExternalServiceError,
    InsufficientStockError,
    InvalidFileError,
    NotFoundError,
    PermissionDeniedError,
    ProductUnavailableError,
)


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (NotFoundError(), 404),
        (AlreadyExistsError(), 409),
        (BusinessRuleError(), 400),
        (InvalidFileError(), 400),
        (AuthenticationError(), 401),
        (PermissionDeniedError(), 403),
        (ExternalServiceError(), 502),
        (ConfigurationError(), 500),
        (AppError(), 500),
        # подклассы наследуют статус родителя
        (EmailAlreadyRegisteredError(), 409),
        (EmptyCartError(), 400),
        (ProductUnavailableError(7), 400),
        (InsufficientStockError("Lamp"), 400),
    ],
)
def test_resolve_status_code(exc: AppError, expected: int) -> None:
    assert resolve_status_code(exc) == expected


def test_default_and_custom_messages() -> None:
    assert NotFoundError().message == "Resource not found"
    assert NotFoundError("Order not found").message == "Order not found"
    assert InsufficientStockError("Lamp").message == "Not enough stock for product Lamp"


def _make_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError("Order not found")

    @app.get("/auth")
    async def auth() -> None:
        raise AuthenticationError("Token has expired")

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internal detail")

    return app


async def test_app_error_is_translated_to_json() -> None:
    transport = ASGITransport(app=_make_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/not-found")

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Order not found", "code": "not_found"}


async def test_authentication_error_has_www_authenticate_header() -> None:
    transport = ASGITransport(app=_make_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/auth")

    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"
    assert resp.json()["code"] == "authentication_failed"


async def test_unexpected_error_does_not_leak_details() -> None:
    transport = ASGITransport(app=_make_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/boom")

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error", "code": "internal_error"}
    assert "secret" not in resp.text

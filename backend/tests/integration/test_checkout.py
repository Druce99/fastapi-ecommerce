"""Оформление заказа: фазы checkout, компенсация при сбое платежа. ЮKassa подменяется."""

from functools import partial

import pytest
from src.repository.uow import SqlAlchemyUnitOfWork
from src.service.orders import OrderService

from tests.integration.conftest import session_maker_test


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _ok_payment(**kwargs):
    return {
        "id": f"pay-{kwargs['order_id']}",
        "status": "pending",
        "confirmation_url": "https://pay.test/confirm",
    }


async def _unavailable_payment(**kwargs):
    raise ConnectionError("yookassa is down")


async def _misconfigured_payment(**kwargs):
    raise RuntimeError("keys are not set")


@pytest.fixture
def payment_ok(monkeypatch):
    monkeypatch.setattr("src.service.orders.create_yookassa_payment", _ok_payment)


@pytest.fixture
def payment_down(monkeypatch):
    monkeypatch.setattr("src.service.orders.create_yookassa_payment", _unavailable_payment)


@pytest.fixture
def payment_misconfigured(monkeypatch):
    monkeypatch.setattr("src.service.orders.create_yookassa_payment", _misconfigured_payment)


async def _add_to_cart(client, token, product_id, quantity):
    resp = await client.post(
        "/cart/items",
        json={"product_id": product_id, "quantity": quantity},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.json()


async def _stock(client, product_id) -> int:
    resp = await client.get(f"/products/{product_id}")
    return resp.json()["stock"]


async def _cart_items(client, token) -> list:
    resp = await client.get("/cart/", headers=_auth(token))
    return resp.json()["items"]


async def _orders(client, token) -> dict:
    resp = await client.get("/orders/", headers=_auth(token))
    return resp.json()


class TestCheckoutSuccess:
    async def test_reserves_stock_creates_pending_order_and_clears_cart(
        self, client, buyer_token, product, payment_ok
    ):
        await _add_to_cart(client, buyer_token, product["id"], 3)

        resp = await client.post("/orders/checkout", headers=_auth(buyer_token))

        assert resp.status_code == 201, resp.json()
        body = resp.json()
        assert body["confirmation_url"] == "https://pay.test/confirm"
        assert body["order"]["status"] == "pending"
        assert body["order"]["payment_id"] == f"pay-{body['order']['id']}"
        assert len(body["order"]["items"]) == 1
        assert body["order"]["items"][0]["quantity"] == 3
        assert await _stock(client, product["id"]) == 7
        assert await _cart_items(client, buyer_token) == []


class TestCheckoutFailures:
    async def test_empty_cart(self, client, buyer_token, payment_ok):
        resp = await client.post("/orders/checkout", headers=_auth(buyer_token))

        assert resp.status_code == 400
        assert resp.json()["code"] == "empty_cart"

    async def test_insufficient_stock_creates_no_order(
        self, client, buyer_token, product, payment_ok
    ):
        await _add_to_cart(client, buyer_token, product["id"], product["stock"] + 1)

        resp = await client.post("/orders/checkout", headers=_auth(buyer_token))

        assert resp.status_code == 400
        assert resp.json()["code"] == "insufficient_stock"
        assert (await _orders(client, buyer_token))["total"] == 0
        assert await _stock(client, product["id"]) == product["stock"]

    async def test_payment_service_down_compensates(
        self, client, buyer_token, product, payment_down
    ):
        await _add_to_cart(client, buyer_token, product["id"], 3)

        resp = await client.post("/orders/checkout", headers=_auth(buyer_token))

        assert resp.status_code == 502
        assert resp.json()["code"] == "external_service_error"
        # остаток возвращён, корзина сохранена, заказ отменён
        assert await _stock(client, product["id"]) == product["stock"]
        cart = await _cart_items(client, buyer_token)
        assert [(i["product"]["id"], i["quantity"]) for i in cart] == [(product["id"], 3)]
        orders = await _orders(client, buyer_token)
        assert orders["total"] == 1
        assert orders["items"][0]["status"] == "canceled"

    async def test_misconfigured_payment_is_server_error_and_compensates(
        self, client, buyer_token, product, payment_misconfigured
    ):
        await _add_to_cart(client, buyer_token, product["id"], 2)

        resp = await client.post("/orders/checkout", headers=_auth(buyer_token))

        assert resp.status_code == 500
        assert resp.json()["code"] == "configuration_error"
        assert await _stock(client, product["id"]) == product["stock"]


class TestCancelPendingOrder:
    async def test_is_idempotent(self, client, buyer_token, product, payment_down):
        await _add_to_cart(client, buyer_token, product["id"], 4)
        await client.post("/orders/checkout", headers=_auth(buyer_token))
        order_id = (await _orders(client, buyer_token))["items"][0]["id"]

        service = OrderService(partial(SqlAlchemyUnitOfWork, session_maker_test))

        # заказ уже отменён компенсацией: повторная отмена ничего не делает
        assert await service.cancel_pending_order(order_id) is False
        assert await _stock(client, product["id"]) == product["stock"]

    async def test_cancels_pending_order_and_restores_stock(
        self, client, buyer_token, product, payment_ok
    ):
        await _add_to_cart(client, buyer_token, product["id"], 4)
        checkout = await client.post("/orders/checkout", headers=_auth(buyer_token))
        order_id = checkout.json()["order"]["id"]
        assert await _stock(client, product["id"]) == product["stock"] - 4

        service = OrderService(partial(SqlAlchemyUnitOfWork, session_maker_test))

        assert await service.cancel_pending_order(order_id) is True
        assert await service.cancel_pending_order(order_id) is False  # второй раз — no-op
        assert await _stock(client, product["id"]) == product["stock"]
        orders = await _orders(client, buyer_token)
        assert orders["items"][0]["status"] == "canceled"

"""Webhook ЮKassa: состояние платежа берётся из API ЮKassa, а не из тела уведомления."""

from decimal import Decimal

import pytest
from src.service.payments import PaymentInfo

WEBHOOK_URL = "/payments/yookassa/webhook"
STOCK_RESERVED = 3


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _ok_payment(**kwargs):
    return {
        "id": f"pay-{kwargs['order_id']}",
        "status": "pending",
        "confirmation_url": "https://pay.test/confirm",
    }


def _event(payment_id: str, event: str = "payment.succeeded") -> dict:
    return {"type": "notification", "event": event, "object": {"id": payment_id}}


@pytest.fixture
async def pending_order(client, buyer_token, product, monkeypatch):
    """Заказ в статусе pending: резерв сделан, платёж «создан» (ЮKassa подменена)."""
    monkeypatch.setattr("src.service.orders.create_yookassa_payment", _ok_payment)
    cart = await client.post(
        "/cart/items",
        json={"product_id": product["id"], "quantity": STOCK_RESERVED},
        headers=_auth(buyer_token),
    )
    assert cart.status_code == 201, cart.json()
    resp = await client.post("/orders/checkout", headers=_auth(buyer_token))
    assert resp.status_code == 201, resp.json()
    order = resp.json()["order"]
    return {
        "id": order["id"],
        "payment_id": order["payment_id"],
        "amount": Decimal(order["total_amount"]),
        "product_id": product["id"],
        "initial_stock": product["stock"],
    }


def _fake_yookassa(monkeypatch, order, *, status="succeeded", **overrides):
    """ЮKassa «отвечает» заданным состоянием платежа."""
    info = PaymentInfo(
        id=order["payment_id"],
        status=status,
        amount=order["amount"],
        currency="RUB",
        order_id=order["id"],
    )
    info = PaymentInfo(**{**info.__dict__, **overrides})

    async def fetch(payment_id: str) -> PaymentInfo:
        return info

    monkeypatch.setattr("src.service.orders.fetch_yookassa_payment", fetch)


async def _order_status(client, token, order_id) -> str:
    resp = await client.get(f"/orders/{order_id}", headers=_auth(token))
    return resp.json()["status"]


async def _stock(client, product_id) -> int:
    return (await client.get(f"/products/{product_id}")).json()["stock"]


async def _notify(client, order, event="payment.succeeded"):
    return await client.post(WEBHOOK_URL, json=_event(order["payment_id"], event))


class TestSucceeded:
    async def test_marks_order_paid(self, client, buyer_token, pending_order, monkeypatch):
        _fake_yookassa(monkeypatch, pending_order, status="succeeded")

        resp = await _notify(client, pending_order)

        assert resp.status_code == 200
        order = (
            await client.get(f"/orders/{pending_order['id']}", headers=_auth(buyer_token))
        ).json()
        assert order["status"] == "paid"
        assert order["paid_at"] is not None
        # остаток остаётся списанным
        stock = await _stock(client, pending_order["product_id"])
        assert stock == pending_order["initial_stock"] - STOCK_RESERVED

    async def test_repeated_notification_is_harmless(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, status="succeeded")

        first = await _notify(client, pending_order)
        second = await _notify(client, pending_order)

        assert first.status_code == second.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "paid"

    async def test_payment_for_canceled_order_does_not_change_it(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, status="canceled")
        await _notify(client, pending_order, "payment.canceled")
        _fake_yookassa(monkeypatch, pending_order, status="succeeded")

        resp = await _notify(client, pending_order)

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "canceled"


class TestCanceled:
    async def test_cancels_order_and_restores_stock(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, status="canceled")

        resp = await _notify(client, pending_order, "payment.canceled")

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "canceled"
        assert await _stock(client, pending_order["product_id"]) == pending_order["initial_stock"]

    async def test_repeated_cancel_restores_stock_once(self, client, pending_order, monkeypatch):
        _fake_yookassa(monkeypatch, pending_order, status="canceled")

        await _notify(client, pending_order, "payment.canceled")
        await _notify(client, pending_order, "payment.canceled")

        assert await _stock(client, pending_order["product_id"]) == pending_order["initial_stock"]

    async def test_paid_order_is_not_canceled(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, status="succeeded")
        await _notify(client, pending_order)
        _fake_yookassa(monkeypatch, pending_order, status="canceled")

        resp = await _notify(client, pending_order, "payment.canceled")

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "paid"
        stock = await _stock(client, pending_order["product_id"])
        assert stock == pending_order["initial_stock"] - STOCK_RESERVED


class TestUntrustedNotifications:
    async def test_amount_mismatch_is_ignored(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, amount=Decimal("1.00"))

        resp = await _notify(client, pending_order)

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "pending"

    async def test_foreign_payment_id_is_ignored(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, id="pay-of-someone-else")

        resp = await client.post(WEBHOOK_URL, json=_event("pay-of-someone-else"))

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "pending"

    async def test_unknown_order_is_ignored(self, client, pending_order, monkeypatch):
        _fake_yookassa(monkeypatch, pending_order, order_id=999999)

        resp = await _notify(client, pending_order)

        assert resp.status_code == 200

    async def test_payment_without_order_id_is_ignored(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, order_id=None)

        resp = await _notify(client, pending_order)

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "pending"

    async def test_unfinished_payment_does_not_change_order(
        self, client, buyer_token, pending_order, monkeypatch
    ):
        _fake_yookassa(monkeypatch, pending_order, status="pending")

        resp = await _notify(client, pending_order)

        assert resp.status_code == 200
        assert await _order_status(client, buyer_token, pending_order["id"]) == "pending"


class TestMalformedRequests:
    async def test_invalid_json(self, client):
        resp = await client.post(
            WEBHOOK_URL, content=b"not json", headers={"Content-Type": "application/json"}
        )

        assert resp.status_code == 400

    @pytest.mark.parametrize(
        "payload",
        [[], {}, {"event": "payment.succeeded"}, {"event": "payment.succeeded", "object": {}}],
    )
    async def test_invalid_structure(self, client, payload):
        resp = await client.post(WEBHOOK_URL, json=payload)

        assert resp.status_code == 400

    async def test_non_payment_event_is_ignored_without_calling_yookassa(self, client, monkeypatch):
        async def must_not_be_called(payment_id: str):
            raise AssertionError("ЮKassa не должна вызываться")

        monkeypatch.setattr("src.service.orders.fetch_yookassa_payment", must_not_be_called)

        resp = await client.post(WEBHOOK_URL, json=_event("rf-1", "refund.succeeded"))

        assert resp.status_code == 200
        assert resp.json() == {"status": "ignored"}

    async def test_yookassa_unavailable_returns_5xx_so_it_retries(self, client, monkeypatch):
        async def down(payment_id: str):
            raise ConnectionError("yookassa is down")

        monkeypatch.setattr("src.service.orders.fetch_yookassa_payment", down)

        resp = await client.post(WEBHOOK_URL, json=_event("pay-1"))

        assert resp.status_code == 502

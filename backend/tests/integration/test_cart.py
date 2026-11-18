from decimal import Decimal

import pytest


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_cart_add_merge_update_and_remove(client, buyer_token, product):
    headers = bearer(buyer_token)
    product_id = product["id"]
    payload = {"product_id": product_id, "quantity": 2}

    first = await client.post("/cart/items", json=payload, headers=headers)
    assert first.status_code == 201, first.text
    assert first.json()["quantity"] == 2

    second = await client.post("/cart/items", json=payload, headers=headers)
    assert second.status_code == 201, second.text
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["quantity"] == 4

    updated = await client.put(f"/cart/items/{product_id}", json={"quantity": 3}, headers=headers)
    assert updated.status_code == 200, updated.text
    assert updated.json()["quantity"] == 3

    cart = await client.get("/cart/", headers=headers)
    assert cart.status_code == 200, cart.text
    body = cart.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["product"]["id"] == product_id
    assert body["total_quantity"] == 3
    assert Decimal(body["total_price"]) == 3 * Decimal(product["price"])

    removed = await client.delete(f"/cart/items/{product_id}", headers=headers)
    assert removed.status_code == 204, removed.text
    cart = await client.get("/cart/", headers=headers)
    assert cart.status_code == 200, cart.text
    assert cart.json()["items"] == []
    assert cart.json()["total_quantity"] == 0
    assert Decimal(cart.json()["total_price"]) == 0


async def test_cart_is_private_and_clear_only_affects_current_user(
    client, buyer_token, seller_token, product
):
    buyer = bearer(buyer_token)
    seller = bearer(seller_token)
    payload = {"product_id": product["id"], "quantity": 1}

    for headers in (buyer, seller):
        added = await client.post("/cart/items", json=payload, headers=headers)
        assert added.status_code == 201, added.text

    cleared = await client.delete("/cart/", headers=buyer)
    assert cleared.status_code == 204, cleared.text
    buyer_cart = await client.get("/cart/", headers=buyer)
    seller_cart = await client.get("/cart/", headers=seller)
    assert buyer_cart.status_code == seller_cart.status_code == 200
    assert buyer_cart.json()["items"] == []
    assert seller_cart.json()["total_quantity"] == 1


@pytest.mark.parametrize("quantity", [0, -1])
async def test_add_rejects_non_positive_quantity(client, buyer_token, product, quantity):
    response = await client.post(
        "/cart/items",
        json={"product_id": product["id"], "quantity": quantity},
        headers=bearer(buyer_token),
    )
    assert response.status_code == 422, response.text
    assert any(error["loc"] == ["body", "quantity"] for error in response.json()["detail"])


async def test_remove_returns_not_found_for_product_outside_cart(client, buyer_token, product):
    response = await client.delete(f"/cart/items/{product['id']}", headers=bearer(buyer_token))
    assert response.status_code == 404, response.text
    assert response.json()["code"] == "not_found"


async def test_cart_requires_authentication(client):
    response = await client.get("/cart/")
    assert response.status_code == 401, response.text

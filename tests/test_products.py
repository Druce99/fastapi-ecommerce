import pytest


class TestGetProducts:
    async def test_get_all_products(self, client):
        resp = await client.get("/products/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_get_product_by_id(self, client, product):
        resp = await client.get(f"/products/{product['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == product["id"]

    async def test_get_nonexistent_product(self, client):
        resp = await client.get("/products/999999")
        assert resp.status_code == 404

    async def test_get_products_by_category(self, client, product, category):
        resp = await client.get(f"/products/category/{category['id']}")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert any(p["id"] == product["id"] for p in resp.json())

    async def test_get_products_by_invalid_category(self, client):
        resp = await client.get("/products/category/999999")
        assert resp.status_code == 404


class TestProductFilters:
    async def test_filter_by_min_price(self, client, product):
        resp = await client.get("/products/", params={"min_price": 0})
        assert resp.status_code == 200

    async def test_filter_invalid_price_range(self, client):
        resp = await client.get("/products/", params={"min_price": 100, "max_price": 50})
        assert resp.status_code == 400

    async def test_filter_in_stock(self, client, product):
        resp = await client.get("/products/", params={"in_stock": True})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["stock"] > 0

    async def test_pagination(self, client):
        resp = await client.get("/products/", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5


class TestCreateProduct:
    async def test_seller_can_create(self, client, seller_token, category):
        resp = await client.post(
            "/products/",
            json={
                "name": "New Product",
                "description": "Some description",
                "price": "49.99",
                "stock": 5,
                "category_id": category["id"],
            },
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Product"
        assert data["is_active"] is True

    async def test_buyer_cannot_create(self, client, buyer_token, category):
        resp = await client.post(
            "/products/",
            json={
                "name": "Buyer Product",
                "description": "desc",
                "price": "10.00",
                "stock": 1,
                "category_id": category["id"],
            },
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 403

    async def test_invalid_category_fails(self, client, seller_token):
        resp = await client.post(
            "/products/",
            json={
                "name": "Bad Product",
                "description": "desc",
                "price": "10.00",
                "stock": 1,
                "category_id": 999999,
            },
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        assert resp.status_code == 400

    async def test_unauthorized_cannot_create(self, client, category):
        resp = await client.post(
            "/products/",
            json={
                "name": "No Auth Product",
                "price": "10.00",
                "stock": 1,
                "category_id": category["id"],
            },
        )
        assert resp.status_code == 401


class TestUpdateProduct:
    async def test_seller_can_update_own_product(self, client, seller_token, product, category):
        resp = await client.put(
            f"/products/{product['id']}",
            json={
                "name": "Updated Product",
                "description": "Updated desc",
                "price": "199.99",
                "stock": 20,
                "category_id": category["id"],
            },
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Product"

    async def test_seller_cannot_update_others_product(self, client, category, product):
        import uuid
        # Второй продавец
        email = f"seller2_{uuid.uuid4().hex[:6]}@test.com"
        await client.post("/users/", json={"email": email, "password": "pass123456", "role": "seller"})
        login = await client.post("/users/token", data={"username": email, "password": "pass123456"})
        other_token = login.json()["access_token"]

        resp = await client.put(
            f"/products/{product['id']}",
            json={
                "name": "Hacked",
                "price": "1.00",
                "stock": 0,
                "category_id": category["id"],
            },
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403


class TestDeleteProduct:
    async def test_seller_can_delete_own_product(self, client, seller_token, category):
        create = await client.post(
            "/products/",
            json={
                "name": "To Delete",
                "description": "desc",
                "price": "10.00",
                "stock": 1,
                "category_id": category["id"],
            },
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        product_id = create.json()["id"]

        resp = await client.delete(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_deleted_product_not_found(self, client, seller_token, category):
        create = await client.post(
            "/products/",
            json={
                "name": "Delete Me",
                "description": "desc",
                "price": "10.00",
                "stock": 1,
                "category_id": category["id"],
            },
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        product_id = create.json()["id"]
        await client.delete(
            f"/products/{product_id}",
            headers={"Authorization": f"Bearer {seller_token}"},
        )

        resp = await client.get(f"/products/{product_id}")
        assert resp.status_code == 404

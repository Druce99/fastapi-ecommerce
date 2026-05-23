import pytest


class TestGetReviews:
    async def test_get_all_reviews(self, client):
        resp = await client.get("/reviews/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_product_reviews(self, client, product):
        resp = await client.get(f"/products/{product['id']}/reviews")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestCreateReview:
    async def test_buyer_can_create_review(self, client, buyer_token, product):
        resp = await client.post(
            "/reviews/",
            json={
                "product_id": product["id"],
                "grade": 5,
                "comment": "Отличный товар!",
            },
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["grade"] == 5
        assert data["product_id"] == product["id"]

    async def test_cannot_review_twice(self, client, buyer_token, product):
        payload = {
            "product_id": product["id"],
            "grade": 4,
            "comment": "Хорошо",
        }
        await client.post(
            "/reviews/",
            json=payload,
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        resp = await client.post(
            "/reviews/",
            json=payload,
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 400

    async def test_seller_cannot_create_review(self, client, seller_token, product):
        resp = await client.post(
            "/reviews/",
            json={"product_id": product["id"], "grade": 3},
            headers={"Authorization": f"Bearer {seller_token}"},
        )
        assert resp.status_code == 403

    async def test_review_nonexistent_product(self, client, buyer_token):
        resp = await client.post(
            "/reviews/",
            json={"product_id": 999999, "grade": 5},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 404

    async def test_invalid_grade(self, client, buyer_token, product):
        resp = await client.post(
            "/reviews/",
            json={"product_id": product["id"], "grade": 10},  # max = 5
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 422


class TestDeleteReview:
    async def test_buyer_can_delete_own_review(self, client, buyer_token, product):
        create = await client.post(
            "/reviews/",
            json={"product_id": product["id"], "grade": 3, "comment": "Норм"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        review_id = create.json()["id"]

        resp = await client.delete(
            f"/reviews/{review_id}",
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 200

    async def test_cannot_delete_others_review(self, client, buyer_token, product):
        import uuid

        # Первый buyer оставляет отзыв
        create = await client.post(
            "/reviews/",
            json={"product_id": product["id"], "grade": 2, "comment": "Плохо"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        review_id = create.json()["id"]

        # Второй buyer пытается удалить
        email = f"buyer2_{uuid.uuid4().hex[:6]}@test.com"
        await client.post("/users/", json={"email": email, "password": "pass123456", "role": "buyer"})
        login = await client.post("/users/token", data={"username": email, "password": "pass123456"})
        other_token = login.json()["access_token"]

        resp = await client.delete(
            f"/reviews/{review_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_can_delete_any_review(self, client, admin_token, buyer_token, product):
        create = await client.post(
            "/reviews/",
            json={"product_id": product["id"], "grade": 1, "comment": "Ужасно"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        review_id = create.json()["id"]

        resp = await client.delete(
            f"/reviews/{review_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200


class TestRatingUpdate:
    async def test_rating_updates_after_review(self, client, buyer_token, product):
        await client.post(
            "/reviews/",
            json={"product_id": product["id"], "grade": 4, "comment": "Хорошо"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        resp = await client.get(f"/products/{product['id']}")
        assert resp.status_code == 200
        assert float(resp.json()["rating"]) == 4.0

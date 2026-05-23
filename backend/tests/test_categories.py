import pytest


class TestGetCategories:
    async def test_get_all_categories(self, client):
        resp = await client.get("/categories/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_category_by_id(self, client, category):
        resp = await client.get(f"/categories/{category['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == category["id"]

    async def test_get_nonexistent_category(self, client):
        resp = await client.get("/categories/999999")
        assert resp.status_code == 404

    async def test_get_root_categories(self, client, category):
        resp = await client.get("/categories/root")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_category_tree(self, client):
        resp = await client.get("/categories/tree")
        assert resp.status_code == 200


class TestCreateCategory:
    async def test_admin_can_create(self, client, admin_token):
        resp = await client.post(
            "/categories/",
            json={"name": "Electronics", "parent_id": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Electronics"

    async def test_create_subcategory(self, client, admin_token, category):
        resp = await client.post(
            "/categories/",
            json={"name": "Subcategory", "parent_id": category["id"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["parent_id"] == category["id"]

    async def test_duplicate_name_fails(self, client, admin_token, category):
        resp = await client.post(
            "/categories/",
            json={"name": category["name"], "parent_id": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_non_admin_cannot_create(self, client, buyer_token):
        resp = await client.post(
            "/categories/",
            json={"name": "Hacked Category", "parent_id": None},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 403

    async def test_unauthorized_cannot_create(self, client):
        resp = await client.post("/categories/", json={"name": "No Auth", "parent_id": None})
        assert resp.status_code == 401


class TestUpdateCategory:
    async def test_admin_can_update(self, client, admin_token, category):
        resp = await client.put(
            f"/categories/{category['id']}",
            json={"name": "Updated Name", "parent_id": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_cannot_be_own_parent(self, client, admin_token, category):
        resp = await client.put(
            f"/categories/{category['id']}",
            json={"name": category["name"], "parent_id": category["id"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400


class TestDeleteCategory:
    async def test_admin_can_delete(self, client, admin_token):
        create = await client.post(
            "/categories/",
            json={"name": "To Delete", "parent_id": None},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        cat_id = create.json()["id"]

        resp = await client.delete(
            f"/categories/{cat_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_cannot_delete_with_children(self, client, admin_token, category):
        await client.post(
            "/categories/",
            json={"name": "Child Category", "parent_id": category["id"]},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = await client.delete(
            f"/categories/{category['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

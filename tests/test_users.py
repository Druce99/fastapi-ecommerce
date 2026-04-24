import pytest


class TestRegister:
    async def test_register_buyer(self, client):
        resp = await client.post("/users/", json={
            "email": "newbuyer@test.com",
            "password": "password123",
            "role": "buyer",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newbuyer@test.com"
        assert data["role"] == "buyer"
        assert data["is_active"] is True

    async def test_register_seller(self, client):
        resp = await client.post("/users/", json={
            "email": "newseller@test.com",
            "password": "password123",
            "role": "seller",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "seller"

    async def test_register_duplicate_email(self, client):
        payload = {"email": "dup@test.com", "password": "password123", "role": "buyer"}
        await client.post("/users/", json=payload)
        resp = await client.post("/users/", json=payload)
        assert resp.status_code == 409

    async def test_register_invalid_role(self, client):
        resp = await client.post("/users/", json={
            "email": "hack@test.com",
            "password": "password123",
            "role": "admin",  # нельзя зарегистрироваться как admin
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, client):
        resp = await client.post("/users/", json={
            "email": "short@test.com",
            "password": "123",
            "role": "buyer",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client):
        await client.post("/users/", json={
            "email": "logintest@test.com",
            "password": "password123",
            "role": "buyer",
        })
        resp = await client.post("/users/token", data={
            "username": "logintest@test.com",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        await client.post("/users/", json={
            "email": "wrongpass@test.com",
            "password": "password123",
            "role": "buyer",
        })
        resp = await client.post("/users/token", data={
            "username": "wrongpass@test.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post("/users/token", data={
            "username": "ghost@test.com",
            "password": "password123",
        })
        assert resp.status_code == 401


class TestTokens:
    async def test_refresh_token(self, client):
        import uuid
        email = f"refresh_{uuid.uuid4().hex[:8]}@test.com"
        await client.post("/users/", json={"email": email, "password": "password123", "role": "buyer"})
        login = await client.post("/users/token", data={"username": email, "password": "password123"})
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/users/refresh-token", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "refresh_token" in resp.json()

    async def test_refresh_access_token(self, client):
        import uuid
        email = f"accessrefresh_{uuid.uuid4().hex[:8]}@test.com"
        await client.post("/users/", json={"email": email, "password": "password123", "role": "buyer"})
        login = await client.post("/users/token", data={"username": email, "password": "password123"})
        refresh_token = login.json()["refresh_token"]

        resp = await client.post("/users/access-token", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_access_token_fails(self, client, buyer_token):
        # access_token нельзя использовать как refresh
        resp = await client.post("/users/refresh-token", json={"refresh_token": buyer_token})
        assert resp.status_code == 401


class TestUpdateRole:
    async def test_admin_can_update_role(self, client, admin_token):
        reg = await client.post("/users/", json={
            "email": "rolechange@test.com",
            "password": "password123",
            "role": "buyer",
        })
        user_id = reg.json()["id"]

        resp = await client.put(
            f"/users/{user_id}/role",
            json={"role": "seller"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "seller"

    async def test_non_admin_cannot_update_role(self, client, buyer_token):
        import uuid
        reg = await client.post("/users/", json={
            "email": f"target_{uuid.uuid4().hex[:8]}@test.com",
            "password": "password123",
            "role": "seller",
        })
        user_id = reg.json()["id"]
        resp = await client.put(
            f"/users/{user_id}/role",
            json={"role": "seller"},
            headers={"Authorization": f"Bearer {buyer_token}"},
        )
        assert resp.status_code == 403

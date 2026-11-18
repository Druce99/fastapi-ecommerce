"""Админка защищена на уровне приложения (а не только nginx)."""

from src.core.config import settings

LOGIN_URL = "/admin/login"


def _credentials(password: str | None = None) -> dict[str, str]:
    return {
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD if password is None else password,
    }


async def test_admin_index_requires_login(client):
    resp = await client.get("/admin/", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"].endswith(LOGIN_URL)


async def test_wrong_password_is_rejected(client):
    resp = await client.post(
        LOGIN_URL, data=_credentials("definitely-wrong"), follow_redirects=False
    )

    assert resp.status_code == 400
    after = await client.get("/admin/", follow_redirects=False)
    assert after.status_code == 302


async def test_wrong_username_is_rejected(client):
    data = {**_credentials(), "username": "not-the-admin"}

    resp = await client.post(LOGIN_URL, data=data, follow_redirects=False)

    assert resp.status_code == 400


async def test_correct_credentials_open_the_admin(client):
    login = await client.post(LOGIN_URL, data=_credentials(), follow_redirects=False)
    assert login.status_code == 302

    resp = await client.get("/admin/", follow_redirects=False)

    assert resp.status_code == 200


async def test_logout_closes_the_session(client):
    await client.post(LOGIN_URL, data=_credentials(), follow_redirects=False)

    logout = await client.get("/admin/logout", follow_redirects=False)
    assert logout.status_code == 302

    resp = await client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 302


async def test_api_admin_token_does_not_grant_access_to_admin_panel(client, admin_token):
    resp = await client.get(
        "/admin/", headers={"Authorization": f"Bearer {admin_token}"}, follow_redirects=False
    )

    assert resp.status_code == 302

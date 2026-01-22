from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.user import User


def test_login_page_renders(client: TestClient) -> None:
    response = client.get("/login")
    assert response.status_code == status.HTTP_200_OK
    assert "Sign In" in response.text


def test_login_success(client: TestClient, test_user: User) -> None:
    response = client.post(
        "/login",
        data={"username": test_user.username, "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/"
    assert settings.SESSION_COOKIE_NAME in response.cookies


def test_login_failure(client: TestClient, test_user: User) -> None:
    response = client.post(
        "/login",
        data={"username": test_user.username, "password": "wrongpassword"},
        follow_redirects=False,
    )
    assert response.status_code == status.HTTP_200_OK
    assert "Invalid credentials" in response.text
    assert settings.SESSION_COOKIE_NAME not in response.cookies


def test_logout(auth_client: TestClient) -> None:
    response = auth_client.get("/logout", follow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"
    # Check if the response deletes the session cookie
    cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
    assert cookie == "" or cookie is None


def test_protected_route_redirect(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers["location"] == "/login"

from fastapi import status
from fastapi.testclient import TestClient

from app.core.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from app.models.user import User


def test_safe_request_issues_a_token(client: TestClient) -> None:
    """The browser needs the cookie before it can echo it back."""
    response = client.get("/login")

    assert response.status_code == status.HTTP_200_OK
    assert client.cookies.get(CSRF_COOKIE_NAME)


def test_json_write_without_a_token_is_refused(auth_client: TestClient) -> None:
    """A cross-site page can send the session cookie but cannot read it."""
    auth_client.headers.pop(CSRF_HEADER_NAME, None)

    response = auth_client.post("/words", json={"word": "test"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_json_write_with_a_mismatched_token_is_refused(
    auth_client: TestClient,
) -> None:
    auth_client.headers[CSRF_HEADER_NAME] = "not-the-cookie-value"

    response = auth_client.post("/words", json={"word": "test"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_form_post_without_a_token_is_refused(
    client: TestClient, test_user: User
) -> None:
    client.get("/login")

    response = client.post(
        "/login",
        data={"username": test_user.username, "password": "testpassword"},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_form_post_with_the_token_succeeds(client: TestClient, test_user: User) -> None:
    client.get("/login")
    token = client.cookies[CSRF_COOKIE_NAME]

    response = client.post(
        "/login",
        data={
            "username": test_user.username,
            "password": "testpassword",
            "csrf_token": token,
        },
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER


def test_login_form_renders_the_token(client: TestClient) -> None:
    """A template typo would silently render an empty value and lock everyone out."""
    response = client.get("/login")
    token = client.cookies[CSRF_COOKIE_NAME]

    assert f'name="csrf_token" value="{token}"' in response.text


def test_logout_form_renders_the_token(auth_client: TestClient) -> None:
    response = auth_client.get("/")
    token = auth_client.cookies[CSRF_COOKIE_NAME]

    assert f'name="csrf_token" value="{token}"' in response.text


def test_reads_need_no_token(auth_client: TestClient) -> None:
    """Only state-changing methods are gated, or every page would break."""
    auth_client.headers.pop(CSRF_HEADER_NAME, None)

    response = auth_client.get("/words")

    assert response.status_code == status.HTTP_200_OK

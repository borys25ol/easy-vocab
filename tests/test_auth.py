import statistics
import time
from datetime import UTC, datetime, timedelta

from fastapi import status
from fastapi.testclient import TestClient
from sqlmodel import Session

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


def test_unknown_username_costs_the_same_as_a_wrong_password(
    client: TestClient, test_user: User
) -> None:
    """Skipping the hash for unknown users leaks which usernames exist.

    Bcrypt dominates the request, so an early return on a missing user makes
    the response an order of magnitude faster and turns login into a username
    oracle. Compare medians as a ratio to stay independent of machine speed.
    """

    def median_seconds(username: str) -> float:
        samples = []
        for _ in range(3):
            start = time.perf_counter()
            client.post(
                "/login",
                data={"username": username, "password": "wrongpassword"},
                follow_redirects=False,
            )
            samples.append(time.perf_counter() - start)
        return statistics.median(samples)

    known = median_seconds(test_user.username)
    unknown = median_seconds("no-such-user")

    assert unknown > known * 0.5, (
        f"unknown user answered in {unknown:.3f}s vs {known:.3f}s for a known one"
    )


def fail_login(client: TestClient, username: str, times: int) -> None:
    for _ in range(times):
        client.post(
            "/login",
            data={"username": username, "password": "wrongpassword"},
            follow_redirects=False,
        )


def test_account_locks_after_repeated_failures(
    client: TestClient, test_user: User
) -> None:
    """Without a lock, an attacker can keep guessing the password forever."""
    fail_login(client, test_user.username, settings.MAX_FAILED_LOGIN_ATTEMPTS)

    response = client.post(
        "/login",
        data={"username": test_user.username, "password": "testpassword"},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_200_OK
    assert settings.SESSION_COOKIE_NAME not in response.cookies


def test_locked_account_reports_the_lock_to_the_right_password(
    client: TestClient, test_user: User
) -> None:
    """Only someone who knows the password learns the account is locked."""
    fail_login(client, test_user.username, settings.MAX_FAILED_LOGIN_ATTEMPTS)

    locked = client.post(
        "/login",
        data={"username": test_user.username, "password": "testpassword"},
        follow_redirects=False,
    )
    wrong = client.post(
        "/login",
        data={"username": test_user.username, "password": "stillwrong"},
        follow_redirects=False,
    )

    assert "Too many failed attempts" in locked.text
    assert "Invalid credentials" in wrong.text
    assert "Too many failed attempts" not in wrong.text


def test_successful_login_clears_the_failure_count(
    client: TestClient, session: Session, test_user: User
) -> None:
    """A user who remembers the password must not accumulate toward a lock."""
    fail_login(client, test_user.username, settings.MAX_FAILED_LOGIN_ATTEMPTS - 1)

    response = client.post(
        "/login",
        data={"username": test_user.username, "password": "testpassword"},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    session.refresh(test_user)
    assert test_user.failed_login_count == 0
    assert test_user.locked_until is None


def test_lock_lifts_once_the_window_passes(
    client: TestClient, session: Session, test_user: User
) -> None:
    """The lock must expire on its own, or a lockout becomes permanent."""
    fail_login(client, test_user.username, settings.MAX_FAILED_LOGIN_ATTEMPTS)

    test_user.locked_until = datetime.now(UTC) - timedelta(minutes=1)
    session.add(test_user)
    session.commit()

    response = client.post(
        "/login",
        data={"username": test_user.username, "password": "testpassword"},
        follow_redirects=False,
    )

    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert settings.SESSION_COOKIE_NAME in response.cookies


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

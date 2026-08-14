from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.deps import get_session
from app.core.config import settings
from app.core.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User
from app.services import genai_service


@pytest.fixture(autouse=True)
def refuse_real_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly rather than call the paid API.

    A test that reaches OpenRouter spends real quota and depends on whatever
    .env the machine happens to have, so the same run behaves differently on
    a laptop and on CI. Tests that need the client replace this stub with
    their own, which works because monkeypatch applies after this fixture.
    """

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "This test reached the real OpenRouter client. Patch "
            "app.api.endpoints.words.get_usage_examples, or "
            "genai_service.OpenAI, in the test itself."
        )

    monkeypatch.setattr(genai_service, "OpenAI", refuse)


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> User:
    user = User(username="testuser", hashed_password=get_password_hash("testpassword"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_user_2")
def test_user_2_fixture(session: Session) -> User:
    user = User(
        username="testuser2", hashed_password=get_password_hash("testpassword2")
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="client_factory")
def client_factory_fixture(
    session: Session,
) -> Generator[Callable[[], TestClient], None, None]:
    """Factory fixture that creates new TestClient instances."""

    def get_session_override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override

    def create_client() -> TestClient:
        return TestClient(app)

    yield create_client
    app.dependency_overrides.clear()


@pytest.fixture(name="client")
def client_fixture(client_factory: Callable[[], TestClient]) -> TestClient:
    return client_factory()


def arm_csrf(client: TestClient) -> TestClient:
    """Do what a browser does: collect the CSRF cookie, then echo it back.

    Writes are rejected without the header, so every authenticated client in
    the suite needs this to reach the endpoint under test.
    """
    client.get("/login")
    client.headers[CSRF_HEADER_NAME] = client.cookies[CSRF_COOKIE_NAME]
    return client


@pytest.fixture(name="auth_client")
def auth_client_fixture(
    client_factory: Callable[[], TestClient], test_user: User
) -> TestClient:
    client = client_factory()
    access_token = create_access_token(
        subject=test_user.username, token_version=test_user.token_version
    )
    client.cookies.update({settings.SESSION_COOKIE_NAME: access_token})
    return arm_csrf(client)


@pytest.fixture(name="auth_client_2")
def auth_client_2_fixture(
    client_factory: Callable[[], TestClient], test_user_2: User
) -> TestClient:
    client = client_factory()
    access_token = create_access_token(
        subject=test_user_2.username, token_version=test_user_2.token_version
    )
    client.cookies.update({settings.SESSION_COOKIE_NAME: access_token})
    return arm_csrf(client)

import asyncio
from collections.abc import Generator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastmcp.exceptions import ToolError
from sqlmodel import Session

from app.core.security import hash_mcp_api_key
from app.models.user import User
from mcp_service.server import UserAuthMiddleware, add_word


def make_request(user: object | None) -> object:
    state = SimpleNamespace(user=user)
    return SimpleNamespace(state=state)


def run_tool(word: str) -> dict[str, Any]:
    result = asyncio.run(add_word.run({"word": word}))
    if result.structured_content is None:
        raise AssertionError("Expected structured content")
    return result.structured_content


PLAINTEXT_KEY = "a-known-mcp-key"


@pytest.fixture(name="mcp_user")
def mcp_user_fixture(session: Session) -> User:
    user = User(
        username="mcpuser",
        hashed_password="irrelevant",
        mcp_api_key_hash=hash_mcp_api_key(PLAINTEXT_KEY),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate(session: Session, presented_key: str | None) -> SimpleNamespace:
    """Drive the MCP middleware and hand back the request it authenticated."""
    headers = {} if presented_key is None else {"EASY_VOCAB_API_KEY": presented_key}
    request = SimpleNamespace(headers=headers, state=SimpleNamespace())

    @contextmanager
    def fake_scope() -> Generator[Session, None, None]:
        yield session

    async def call_next(context: Any) -> str:
        return "called"

    with (
        patch("mcp_service.server.get_http_request", return_value=request),
        patch("mcp_service.server.session_scope", fake_scope),
    ):
        middleware = UserAuthMiddleware()
        result = asyncio.run(middleware.on_call_tool(cast(Any, None), call_next))

    assert result == "called"
    return request


def test_mcp_key_is_not_stored_in_plaintext(mcp_user: User) -> None:
    """A database dump must not hand over working MCP keys."""
    stored = mcp_user.mcp_api_key_hash
    assert stored is not None
    assert stored != PLAINTEXT_KEY
    assert PLAINTEXT_KEY not in stored


def test_mcp_auth_accepts_the_plaintext_key(session: Session, mcp_user: User) -> None:
    """Clients keep sending the key they were given; the server hashes it."""
    request = authenticate(session, PLAINTEXT_KEY)

    assert request.state.user.username == mcp_user.username


def test_mcp_auth_rejects_an_unknown_key(session: Session, mcp_user: User) -> None:
    with pytest.raises(ToolError):
        authenticate(session, "not-the-key")


def test_mcp_auth_rejects_a_missing_key(session: Session, mcp_user: User) -> None:
    with pytest.raises(ToolError):
        authenticate(session, None)


def test_mcp_auth_rejects_the_stored_hash_itself(
    session: Session, mcp_user: User
) -> None:
    """Someone holding a leaked hash must not be able to replay it as the key."""
    with pytest.raises(ToolError):
        authenticate(session, mcp_user.mcp_api_key_hash)


def test_add_word_propagates_tool_error() -> None:
    request = make_request(user=None)
    with patch("mcp_service.server.get_http_request", return_value=request):
        with pytest.raises(ToolError):
            asyncio.run(add_word.run({"word": "test"}))


def test_add_word_returns_http_exception_detail() -> None:
    request = make_request(user=SimpleNamespace(id=1))
    with patch("mcp_service.server.get_http_request", return_value=request):
        with patch(
            "mcp_service.server.get_usage_examples",
            side_effect=HTTPException(status_code=400, detail="bad"),
        ):
            response = run_tool("test")
    assert response == {"error": "bad"}


def test_add_word_returns_generic_error_message() -> None:
    request = make_request(user=SimpleNamespace(id=1))
    with patch("mcp_service.server.get_http_request", return_value=request):
        with patch(
            "mcp_service.server.get_usage_examples",
            side_effect=Exception("boom"),
        ):
            with patch("mcp_service.server.logger") as logger:
                response = run_tool("test")

    assert response == {"error": "Failed to add word. Please try again."}
    logger.exception.assert_called_once_with("Unexpected error adding word")

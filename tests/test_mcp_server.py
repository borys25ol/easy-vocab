import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastmcp.exceptions import ToolError

from mcp_service.server import add_word


def make_request(user: object | None) -> object:
    state = SimpleNamespace(user=user)
    return SimpleNamespace(state=state)


def run_tool(word: str) -> dict[str, Any]:
    result = asyncio.run(add_word.run({"word": word}))
    if result.structured_content is None:
        raise AssertionError("Expected structured content")
    return result.structured_content


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

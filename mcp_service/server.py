from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext
from sqlmodel import select

from app.core.config import settings
from app.core.database import session_scope
from app.models.user import User
from app.models.word import Word
from app.services.genai_service import get_usage_examples


class UserAuthMiddleware(Middleware):
    async def on_call_tool(
        self, context: MiddlewareContext, call_next: Callable
    ) -> Any:
        """Validate token in headers or query params before tool execution."""
        request = get_http_request()

        token = request.headers.get("EASY_VOCAB_API_KEY")

        if not token:
            raise ToolError("Access denied: Invalid or missing token")

        with session_scope() as session:
            statement = select(User).where(User.mcp_api_key == token)
            user = session.exec(statement).first()

        if not user:
            raise ToolError("Access denied: Invalid or missing token")

        request.state.user = user

        return await call_next(context)


mcp = FastMCP(name="Words Learning Server")
mcp.add_middleware(UserAuthMiddleware())


@mcp.tool()
def add_word(word: str) -> dict:
    """
    Add a new word to the learning database.
    Automatically fetches translation, examples, and metadata using AI.

    Args:
        word: The word or phrase to add (e.g., "ephemeral", "take off", "break the ice")

    Returns:
        Dictionary with the created word details including translation and examples
    """
    try:
        request = get_http_request()
        user = getattr(request.state, "user", None)
        if not user or user.id is None:
            raise ToolError("Access denied: Invalid or missing token")

        word_info = get_usage_examples(word=word.lower())

        with session_scope() as session:
            new_word = Word.from_dict(
                data=word_info,
                user_id=user.id,
            )
            session.add(new_word)
            session.commit()
            session.refresh(new_word)

            return new_word.to_dict()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="http", host=settings.MCP_HOST, port=settings.MCP_PORT)

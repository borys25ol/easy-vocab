from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext

from app.core.config import settings
from app.core.database import get_session
from app.models.word import Word
from app.services.genai_service import get_usage_examples


class UserAuthMiddleware(Middleware):
    async def on_call_tool(
        self, context: MiddlewareContext, call_next: Callable
    ) -> Any:
        """Validate token in headers or query params before tool execution."""
        request = get_http_request()

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif auth_header:
            token = auth_header
        else:
            token = None

        if not token or token != settings.MCP_API_KEY:
            raise ToolError("Access denied: Invalid or missing token")

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
        word_info = get_usage_examples(word=word.lower())

        with next(get_session()) as session:
            new_word = Word.from_dict(data=word_info)
            session.add(new_word)
            session.commit()
            session.refresh(new_word)

            return {
                "id": new_word.id,
                "word": new_word.word,
                "translation": new_word.translation,
                "level": new_word.level,
                "category": new_word.category,
                "type": new_word.type,
                "examples": new_word.examples,
                "synonyms": new_word.synonyms,
                "is_phrasal": new_word.is_phrasal,
                "is_idiom": new_word.is_idiom,
                "is_learned": new_word.is_learned,
            }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="http", host=settings.MCP_HOST, port=settings.MCP_PORT)

from fastmcp import FastMCP

from app.core.database import get_session
from app.models.word import Word
from app.services.genai_service import get_usage_examples

MCP_PORT = 6432

mcp = FastMCP(name="Words Learning Server")


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
                "examples": new_word.examples,
                "synonyms": new_word.synonyms,
                "is_learned": new_word.is_learned,
            }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="http", port=MCP_PORT)

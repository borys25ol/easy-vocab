# MCP Server Configuration for Claude Desktop

To use this MCP server with the Cursor use this configuration JSON:

```json
{
  "mcpServers": {
    "easy-vocab-mcp": {
      "type": "http",
      "url": "http://localhost:6432/mcp",
      "enabled": true,
      "timeout": 30000,
      "headers": {}
    }
  }
}
```

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure environment variables are set in `.env`:
   - `GEMINI_API_KEY` - Your Google Gemini API key
   - `GEMINI_MODEL` - Model to use (e.g., `gemini-2.5-flash`)

## Running the Server

```bash
python mcp_server.py
```

## Available Tools

- `add_word(word: str)` - Add a new word to the learning database. Automatically fetches translation, examples, and metadata using AI.

### Example Usage
```
Please add the word "ephemeral" to my learning database.
```

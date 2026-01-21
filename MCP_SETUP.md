# MCP Server Configuration for Claude Desktop

To use this MCP server add this configuration to your config file:

```json
{
  "mcpServers": {
    "easy-vocab-mcp": {
      "type": "http",
      "url": "http://localhost:6432",
      "enabled": true,
      "timeout": 30000
    }
  }
}
```

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** in `.env` file:
   - **AI & APIs**: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`
   - **Database**: `POSTGRES_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`
   - **Security & Authentication**: `SECRET_KEY`
   - **MCP Configuration**: `MCP_PORT`, `MCP_HOST`

3. **Set up PostgreSQL database:**
   - **Option A - Local Docker:**
     ```bash
     docker-compose up postgres
     ```
   - **Option B - External database:** Configure connection in `.env` file

## Running the Server

### Local Development
```bash
python mcp_server.py
```

The server will start on `http://0.0.0.0:6432`

### Docker
```bash
docker-compose up mcp
```

Or run all services:
```bash
docker-compose up
```

## Available Tools

### `add_word(word: str)`
Add a new word or phrase to the learning database. Automatically fetches translation, examples, and metadata using AI.

**Parameters:**
- `word` (str): The word or phrase to add
  - Examples: `"ephemeral"`, `"take off"`, `"break the ice"`

**Returns:**
Dictionary with the created word details:
```python
{
  "id": int,              # Word ID in database
  "word": str,            # Word/phrase text
  "translation": str,     # Ukrainian translation
  "level": str,           # CEFR level (A1-C2)
  "category": str,        # Word category (vocabulary, phrasal, idiom)
  "type": str,            # Word type (noun, verb, adjective, etc.)
  "examples": list[str],  # Usage examples
  "synonyms": list[str],  # Related words
  "is_phrasal": bool,     # Whether word is a phrasal verb
  "is_idiom": bool,       # Whether word is an idiom
  "is_learned": bool      # Learning status
}
```

### Example Usage
```
Please add the word "ephemeral" to my learning database.
```
```
Add the phrasal verb "take off" with its meanings.
```
```
Can you add the idiom "break the ice"?
```

## Server Details

- **Transport**: HTTP
- **Host**: Configurable via `.env` (default: `0.0.0.0`)
- **Port**: Configurable via `.env` (default: `6432`)
- **Framework**: FastMCP
- **Database**: PostgreSQL (shared with main app)

## MCP API Keys

Each user has a unique MCP API key generated via CLI. Pass it in the
`EASY_VOCAB_API_KEY` header for MCP requests.

### Create a user (prints key once)
```bash
python manage.py create-user --username <name> --password <password>
```

### Rotate a user's MCP key
```bash
python manage.py rotate-mcp-key --username <name>
```

### Backfill keys for existing users
```bash
python manage.py backfill-mcp-keys
```

### Migration for existing databases

```bash
uv run python -m scripts.add_user_mcp_api_key
```

## Troubleshooting

### Server won't start
- Ensure `.env` file exists with all required variables
- Check PostgreSQL is running and accessible
- Verify dependencies are installed: `pip install -r requirements.txt`

### Database connection errors
- Check PostgreSQL credentials in `.env`
- Ensure PostgreSQL service is running
- For Docker: Ensure both services are on same network

### MCP tools not showing in Claude Desktop
- Verify server is running on port 6432
- Check Claude Desktop config file syntax
- Restart Claude Desktop after configuration changes
- Check server logs for errors

### View Logs
```bash
# Local
python mcp_server.py

# Docker
docker-compose logs -f mcp
```

## Architecture

The MCP server integrates with:
- **FastMCP**: MCP protocol implementation
- **GenAI Service**: Fetches word enrichment via OpenRouter (Google Gemini)
- **SQLModel**: Database ORM (shares models with main app)
- **PostgreSQL**: Persistent storage

### Flow
1. User requests to add a word via Claude Desktop
2. MCP server receives request through HTTP transport
3. GenAI service enriches word with translation, examples, metadata
4. Word is saved to PostgreSQL database
5. Response returned to Claude Desktop

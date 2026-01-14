# AGENTS.md

## 📋 Project Overview

EasyVocab is an AI-powered English vocabulary builder using Google Gemini AI. It automatically enriches words with Ukrainian translations, usage examples, CEFR levels, and frequency rankings.

**Tech Stack:**
- Backend: Python 3.12+, FastAPI, SQLModel (SQLite)
- AI: Google Gemini via `google-genai` SDK
- Frontend: Jinja2, Tailwind CSS, Vanilla JavaScript
- MCP: FastMCP (HTTP transport on port 6432)

---

## 🏗️ Architecture

```
easy-words-learning/
├── app/
│   ├── api/endpoints/    # FastAPI route handlers
│   ├── core/            # Config, database
│   ├── models/          # SQLModel schemas
│   ├── services/        # Business logic (GenAI service)
│   └── main.py         # Application entry point
├── templates/           # Jinja2 HTML templates
├── static/              # CSS, JS, assets
├── mcp_server.py        # MCP server (FastMCP)
└── tests/               # Pytest test suite
```

**Components:**
- **API Layer**: REST endpoints for words CRUD and HTML pages
- **Service Layer**: `genai_service.py` handles AI word enrichment
- **Data Layer**: SQLite with SQLModel ORM
- **Frontend**: Server-side rendering with Jinja2

---

## 🎨 Code Style Guide

### Python Style
- Line length: 79 characters (Black)
- Type hints: Required for function signatures
- Docstrings: NOT forced (DXXX errors disabled)
- Quotes: Single quotes preferred
- F-strings: Allowed and encouraged
- Imports: Auto-sorted with isort

### Pre-commit Hooks
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting (complexity, quality)
- **mypy**: Type checking
- **pyupgrade**: Python 3.12+ syntax

### Code Quality Settings
- Max complexity: 15 (flake8)
- Python version: 3.12
- Many flake8 rules disabled for flexibility

---

## 🔧 Development Workflow

### Setup
```bash
make ve           # Create venv and install dependencies
```

### Running the App
```bash
make runserver    # FastAPI on http://0.0.0.0:5000
python mcp_server.py  # MCP server on http://localhost:6432
```

### Common Commands
```bash
make style        # Check style without formatting
make format       # Format with black
make lint         # Run linting checks
make types        # Run mypy type checking
make test         # Run pytest
make run_hooks    # Run pre-commit hooks on all files
```

---

## 🧪 Testing

### Test Structure
- Located in `tests/` directory
- Uses pytest framework
- Test client from `fastapi.testclient`
- Mock external services (e.g., `get_usage_examples`)

### Writing Tests
- Use `@patch` decorator for mocking
- Test endpoints with `client.get()`, `client.post()`
- Assert status codes and response structure
- See `tests/test_api_words.py` for examples

### Running Tests
```bash
make test         # Run all tests
pytest           # Direct pytest command
```

---

## 📡 API Documentation

### Words Endpoints
- `GET /words/` - List all words (ordered by created_at desc)
- `POST /words/?word=<text>` - Create new word (AI enriches automatically)
- `PUT /words/{id}` - Update word
- `DELETE /words/{id}` - Delete word
- `PATCH /words/{id}/toggle_learned` - Toggle learned status

### Special Endpoints
- `GET /words/phrasal_roots` - Get unique phrasal verb roots
- `GET /words/phrasal/{root}` - Get phrasal verbs by root
- `GET /words/idioms` - Get all idioms

### Pages Endpoints (HTML)
- `GET /` - Main dashboard
- `GET /quiz` - Quiz page
- `GET /quiz_translate` - Translation quiz
- `GET /flashcards` - Flashcard learning
- `GET /phrasal` - Phrasal verbs explorer
- `GET /idioms` - Idioms list

---

## 🤖 MCP Server

### Purpose
Allows AI assistants to add words directly to the database via MCP protocol.

### Implementation
- Uses FastMCP library
- Single tool: `add_word(word: str)`
- HTTP transport on port 6432
- Direct database access (no API layer)

### Usage
```bash
python mcp_server.py  # Server starts on http://localhost:6432
```

### Tool Signature
```python
add_word(word: str) -> dict
```
Returns: Word details including id, word, translation, level, category, examples, synonyms, is_learned

---

## ⚙️ Configuration

### Environment Variables
Required in `.env` file:
```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
SQLITE_FILE_NAME=words_app.db  # Optional, default provided
```

### Settings Pattern
Uses `pydantic-settings.BaseSettings` in `app/core/config.py`:
- Auto-loads from `.env` file
- `DATABASE_URL` computed property for SQLite connection
- Singleton `settings` instance exported

---

## 🎯 Development Guidelines

### Adding New Features
1. Add route to appropriate endpoint file
2. Implement business logic in service layer if needed
3. Update database models if schema changes
4. Add tests for new functionality
5. Run `make style`, `make types`, `make test` before committing

### Database Changes
- Modify `app/models/*.py` SQLModel classes
- Run `make runserver` - tables auto-created on startup
- SQLite file: `words_app.db` (project root)

### Frontend Updates
- Edit HTML in `templates/`
- Update CSS in `static/css/`
- Update JS in `static/js/`
- Server restart required for changes

### API Development
- Use FastAPI dependency injection with `Depends(get_session)`
- Return appropriate HTTP status codes (200, 404, etc.)
- Document with docstrings (optional but recommended)

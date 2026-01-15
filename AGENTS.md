# AGENTS.md

## 📋 Project Overview

EasyVocab is an AI-powered English vocabulary builder using Google Gemini AI. It automatically enriches words with Ukrainian translations, usage examples, CEFR levels, and frequency rankings.

**Tech Stack:**
- Backend: Python 3.12+, FastAPI, SQLModel (PostgreSQL)
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
├── tests/               # Pytest test suite
├── Dockerfile            # Multi-stage Docker image (builder + runtime)
├── docker-compose.yml    # Local development with PostgreSQL
├── docker-compose.prod.yml  # Production with external PostgreSQL
└── .dockerignore        # Build optimizations
```

**Components:**
- **API Layer**: REST endpoints for words CRUD and HTML pages
- **Service Layer**: `genai_service.py` handles AI word enrichment
- **Data Layer**: PostgreSQL with SQLModel ORM
- **Frontend**: Server-side rendering with Jinja2
- **Docker**: Multi-stage build with non-root user (appuser:1000)
- **Networks**: Bridge network for service isolation
- **Healthchecks**: Integrated health checks for all services

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

#### Local Development
```bash
make ve           # Create venv and install dependencies
```

#### Docker Development
```bash
docker-compose up  # Start all services (web, mcp, postgres)
```

### Running the App
```bash
make runserver    # FastAPI on http://0.0.0.0:5000
python mcp_server.py  # MCP server on http://localhost:6432
```

### Docker Deployment

#### Local Development
```bash
make docker-up    # Start services in foreground
make docker-up-d  # Start in background
make docker-logs  # View logs
make docker-down  # Stop and remove containers
```

#### Production
```bash
make docker-prod-build   # Build production Docker images
make docker-prod-up      # Start production services (external PostgreSQL)
make docker-prod-down    # Stop production services
make docker-prod-logs    # View production logs
```

### Common Commands
```bash
# Code Quality
make style        # Check style without formatting
make format       # Format with black
make lint         # Run linting checks
make types        # Run mypy type checking
make test         # Run pytest
make run_hooks    # Run pre-commit hooks on all files

# Docker
make docker-build      # Build Docker images
make docker-up        # Start local services
make docker-down      # Stop local services
make docker-logs      # View local logs
make docker-prod-up   # Start production services
make docker-prod-down # Stop production services
make docker-prod-logs # View production logs
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

> **Note**: Tests use SQLite in-memory database for fast, isolated testing.

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
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=app
POSTGRES_PORT=5432
```

### Settings Pattern
Uses `pydantic-settings.BaseSettings` in `app/core/config.py`:
- Auto-loads from `.env` file
- `DATABASE_URL` computed property for PostgreSQL connection
- Singleton `settings` instance exported

### Docker Configuration

#### Local Development
- Uses dockerized PostgreSQL (postgres:16-alpine)
- Environment loaded from `.env` file
- Services connect via bridge network (`easyvocab-network`)
- PostgreSQL service uses default credentials (app/postgres/postgres)
- Override `POSTGRES_HOST=postgres` for web/mcp services

#### Production
- Uses external PostgreSQL (e.g., Neon.tech)
- Environment loaded from `.env.production` file
- No PostgreSQL container (external database)
- Resource limits: web (1 CPU, 512MB), mcp (0.5 CPU, 256MB)
- Logging: JSON driver with rotation (10MB max, 3 files)

#### Docker Environment Files
- `.env` - Local development (contains Neon credentials)
- `.env.production` - Production configuration (NEVER commit)

### Healthchecks

All Docker services include health checks:
- **PostgreSQL**: `pg_isready` (10s interval, 5s timeout, 5 retries)
- **Web**: HTTP GET `/` (30s interval, 10s timeout, 3 retries, 40s start period)

Services with `depends_on` wait for health checks before starting.

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
- Run `make runserver` - tables auto-created on startup via SQLModel
- Docker: `docker-compose up` - tables auto-created on startup

### Docker Development

#### Building Images
```bash
docker-compose build              # Rebuild local images
docker-compose build --no-cache   # Clean rebuild
```

#### Managing Containers
```bash
docker-compose ps          # List running containers
docker-compose top         # Show processes
docker-compose logs web    # View web service logs
docker-compose exec web bash  # Access container shell
```

#### Troubleshooting
```bash
# View container logs
docker-compose logs -f web
docker-compose logs -f mcp

# Restart services
docker-compose restart web

# Remove all containers and volumes
docker-compose down -v

# Check health status
docker inspect easyvocab-web | grep -A 10 Health
```

### Frontend Updates
- Edit HTML in `templates/`
- Update CSS in `static/css/`
- Update JS in `static/js/`
- Server restart required for changes

### API Development
- Use FastAPI dependency injection with `Depends(get_session)`
- Return appropriate HTTP status codes (200, 404, etc.)
- Document with docstrings (optional but recommended)

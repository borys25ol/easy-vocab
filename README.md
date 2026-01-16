# EasyVocab 🚀

> An intelligent AI-powered English vocabulary builder that makes learning new words and phrasal verbs effortless.

## What is EasyVocab?

EasyVocab is a smart learning companion designed to streamline vocabulary acquisition. By leveraging **OpenRouter AI gateway (Google Gemini models)**, it automatically enriches every word you add with Ukrainian translations, real-life usage examples, CEFR level classifications, and frequency rankings. Whether you're learning everyday vocabulary, phrasal verbs, or idioms, EasyVocab helps you track progress and master English at your own pace.

## ✨ Key Features

### 🤖 Smart Word Enrichment
- **Auto-generated translations**: Get instant Ukrainian translations for every word
- **Contextual examples**: Learn through real-life usage scenarios
- **Synonym suggestions**: Expand your vocabulary with related words
- **AI-powered**: All metadata generated automatically using OpenRouter

### 📊 Progress Tracking
- **CEFR leveling**: Words categorized from A1 (beginner) to C2 (advanced)
- **Frequency rankings**: Visual badges showing word rarity (Core 500, Active Basic, Rare, etc.)
- **Learned status**: Mark words as mastered to track your progress

### 📚 Comprehensive Learning Tools
- **Phrasal verb explorer**: Study phrasal verbs grouped by root (get, take, look, go)
- **Idiom collection**: Learn common idiomatic expressions with examples
- **Interactive flashcards**: Test yourself with UA→EN and EN→UA quiz modes
- **Audio pronunciation**: Hear correct pronunciation with text-to-speech

### 🎨 User Experience
- **Clean, minimalist design**: Focus on what matters—learning
- **Mobile-friendly**: Learn on any device
- **Color-coded difficulty**: Quick visual cues for word complexity
- **Fast and responsive**: Built with modern web technologies

## 📸 App Screenshots

| Main Dashboard | Phrasal Verbs Explorer | Word Card Details | Flashcard Mode |
|:---:|:---:|:---:|:---:|
| <img src="assets/main.png" width="300"> | <img src="assets/phrasal.png" width="300"> | <img src="assets/card.png" width="300"> | <img src="assets/flashcard.png" width="300"> |
| View all your words in a clean, organized list with progress tracking. | Explore phrasal verbs grouped by root verbs (get, take, look, go) with contextual examples. | See detailed information for each word including translations, examples, and synonyms. | Test your knowledge with interactive flashcards in both UA→EN and EN→UA modes. |

## 🚀 Development Approach

This project was built using **AI-assisted development** with **OpenRouter AI gateway** as a key contributor. Rather than writing boilerplate code and configuration manually, Gemini helped accelerate development by:

- Shaping the application architecture
- Refining core business logic
- Polishing the user interface
- Suggesting best practices and optimizations

This approach allowed for rapid iteration while focusing on delivering an excellent vocabulary learning experience.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLModel (PostgreSQL).
- **AI Engine**: OpenRouter (Google Gemini models via OpenAI SDK).
- **Frontend**: Tailwind CSS, Vanilla JavaScript.
- **Templating**: Jinja2.

## 🚀 Getting Started

### Prerequisites

#### Local Development
- Python 3.12+
- OpenRouter API Key (get it at [OpenRouter](https://openrouter.ai/keys))
- Model name in format `google/gemini-2.5-flash`

#### Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+
- OpenRouter API Key
- PostgreSQL database (local container or external like Neon.tech)

### Installation

#### Option 1: Local Development
1. **Clone the repository**:
    ```bash
    git clone https://github.com/borys25ol/easy-vocab.git
    cd easy-vocab
    ```

2. **Set up a virtual environment**:
    ```bash
    python -m venv .ve
    source .ve/bin/activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure Environment Variables**:
    Create a `.env` file or export the variables directly:
     ```bash
      export OPENROUTER_API_KEY='your_api_key_here'
      export OPENROUTER_MODEL='google/gemini-2.5-flash'
      export POSTGRES_HOST='localhost'
      export POSTGRES_USER='postgres'
      export POSTGRES_PASSWORD='your_password'
      export POSTGRES_DB='app'
      export POSTGRES_PORT='5432'
      ```

#### Option 2: Docker Deployment

**Local Development (Dockerized PostgreSQL):**
```bash
# Clone the repository
git clone https://github.com/borys25ol/easy-vocab.git
cd easy-vocab

# Copy environment template
cp .env.example .env

# Update .env.production with your credentials
nano .env

# Start all services (web, mcp, postgres)
make docker-up

# Or run in background
make docker-up-d
```

**Production (External PostgreSQL):**
```bash
# Clone the repository
git clone https://github.com/borys25ol/easy-vocab.git
cd easy-vocab

# Copy environment template
cp .env.example .env.production

# Update .env.production with your credentials
nano .env.production

# Start production services
make docker-prod-up
```

### Running App

#### Local Development
Start the FastAPI server using the provided `Makefile`:

```bash
# Using Makefile
make runserver

# OR directly
uvicorn app.main:app --reload
```

#### Docker Deployment

**Local Development:**
```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

**Production:**
```bash
# Start production services
make docker-prod-up

# View logs
make docker-prod-logs

# Stop services
make docker-prod-down
```


## 🤖 MCP Server Integration

This project includes an **MCP (Model Context Protocol) server** that allows AI assistants to directly add words to your vocabulary database.

### Features

- **Single `add_word` tool** - Simply provide a word and let AI handle translations, examples, and metadata
- Uses FastMCP for clean, Pythonic implementation
- HTTP transport on port 6432 for easy integration

### Installation

MCP requires the `fastmcp` package (already in `requirements.txt`):

```bash
pip install fastmcp
```

### Running the MCP Server

```bash
python mcp_server.py
```

The server will start on `http://localhost:6432`

### Available Tools

| Tool | Description |
|------|-------------|
| `add_word(word: str)` | Add a new word with auto-generated translations, examples, and metadata |

## 🧪 Testing

Tests use an in-memory SQLite database for fast, isolated testing. No PostgreSQL database is required for running the test suite.

## 🐳 Docker Architecture

### Multi-Stage Build

EasyVocab uses a **multi-stage Docker build** for optimal image size and security:

**Stage 1: Builder**
- Base: `python:3.12-slim`
- Installs build dependencies (gcc, libpq-dev)
- Creates virtual environment at `/opt/venv`
- Installs Python packages from `requirements.txt`

**Stage 2: Runtime**
- Base: `python:3.12-slim`
- Creates non-root user (`appuser:1000`)
- Installs runtime dependencies (postgresql-client, curl)
- Copies Python packages from builder stage
- Copies application code with proper ownership
- Runs as non-root user

**Benefits:**
- ~30% smaller image size (no build tools in runtime)
- Enhanced security (non-root user)
- Faster deployments (smaller images)
- Healthchecks integrated for all services

### Services

#### Local Development
- **web**: FastAPI application (port 5000)
- **mcp**: MCP server (port 6432)
- **postgres**: PostgreSQL 16 database (port 5432)
- **Network**: Bridge network (`easyvocab-network`)
- **Volume**: Named volume for PostgreSQL data persistence

#### Production
- **web**: FastAPI application (port 5000)
- **mcp**: MCP server (port 6432)
- **Database**: External PostgreSQL (e.g., Neon.tech)
- **Network**: Bridge network (`easyvocab-network`)
- **Logging**: JSON driver with rotation (10MB max, 3 files)
- **Resources**: CPU and memory limits configured

### Environment Files

- **`.env`** - Local development (contains your credentials)
- **`.env.production`** - Production configuration (NEVER commit to Git)

### Makefile Commands

```bash
# Local Development
make docker-build      # Build Docker images
make docker-up         # Start services
make docker-down       # Stop services
make docker-logs       # View logs

# Production
make docker-prod-build  # Build production Docker images
make docker-prod-up     # Start production services
make docker-prod-down   # Stop production services
make docker-prod-logs   # View production logs
```

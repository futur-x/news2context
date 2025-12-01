# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

News2Context v2.0 is an AI-driven intelligent news aggregation system that supports multi-task isolation, CLI agent interaction, REST API, and scheduled tasks. The system collects news from various sources (TopHub, RSS, etc.), stores them in a Weaviate vector database, and provides semantic search capabilities.

## Development Commands

### Environment Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### Infrastructure

```bash
# Start Weaviate database (required)
docker-compose up -d

# Verify infrastructure
python test_infrastructure.py
```

### Backend (API Server)

```bash
# Run API server (development with auto-reload)
python -m src.api.app
# Or using uvicorn directly:
uvicorn src.api.app:app --host 0.0.0.0 --port 8043 --reload

# API will be available at: http://localhost:8043
# API docs at: http://localhost:8043/docs
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### CLI Commands

```bash
# Main CLI entry point
python -m src.cli.main

# Interactive news collection
python -m src.cli.main collect

# Chat/query interface
python -m src.cli.main chat

# Task management
python -m src.cli.main task list
python -m src.cli.main task create
python -m src.cli.main task delete <task-name>

# Schedule management
python -m src.cli.main schedule create
python -m src.cli.main schedule list

# Daemon (background scheduler)
python -m src.cli.main daemon start
python -m src.cli.main daemon stop

# Re-run collection for a task
python -m src.cli.main rerun <task-name>
```

### Testing

```bash
# Test infrastructure (Weaviate, API connectivity)
python test_infrastructure.py

# Test specific API endpoints
python test_api.py
python test_tasks_api.py
python test_settings_api.py
python test_external_api.py

# Test search functionality
python test_search.py

# Test chunking system
python test_chunking.py
```

## Architecture

### Core Components

**1. Task Management System (`src/core/task_manager.py`)**
- Each task is isolated with its own configuration and Weaviate collection
- Task configs stored in `config/schedules/*.yaml`
- Tasks are locked by default to prevent accidental modification
- Collection names are generated using UUIDs for uniqueness: `Task_<uuid>`

**2. Weaviate Vector Database (`src/storage/weaviate_client.py`)**
- Two schema types: `NewsArticle` (deprecated) and `NewsChunk` (current)
- Full articles are stored without chunking by default
- Uses OpenAI `text-embedding-3-large` model (3072 dimensions) via LiteLLM proxy
- Fields vectorized: title, content, source_name, category, excerpt
- Fields skipped in vectorization: url, task_name, source_hashid, dates
- Maximum content length: ~30,000 characters (~8,000 tokens)
- Batch insert with size of 20 (articles) or 5 (chunks)

**3. News Collection Engine (`src/engines/`)**
- Plugin-based architecture with factory pattern
- TopHub engine is the primary implementation
- Extractor uses multiple strategies (trafilatura, newspaper3k, BeautifulSoup) with early stopping
- Supports `max_news_per_source` and `early_stop_threshold` for efficiency

**4. Scheduler System (`src/scheduler/daemon.py`)**
- Uses APScheduler with BlockingScheduler
- Loads jobs from task configs with cron expressions
- Auto-reloads task configurations every minute
- Supports minute-precision cron (format: `minute hour day month day_of_week`)

**5. REST API (`src/api/app.py`)**
- FastAPI application running on port 8043
- Routes organized by domain: health, tasks, query, settings, external, chat, browse, sources
- CORS enabled for all origins (adjust for production)
- Frontend served as a separate Vite app on port 5173

### Configuration System

**Primary config: `config/config.yaml`**
- LLM settings: model, API key, base URL (defaults to LiteLLM proxy)
- Embedding settings: model, dimensions (1536 for text-embedding-3-small)
- Weaviate: URL (http://localhost:8080), batch size, chunking options
- News sources: active engine, collector settings
- Logging: level, format, file path

**Task configs: `config/schedules/*.yaml`**
Each task config includes:
- name, scene (user context), sources list
- schedule: cron expression, date_range
- weaviate: collection name
- status: enabled, last_run, progress, running flag
- locked: true (prevents accidental modification)

**Environment variables: `config/.env`**
- API keys for OpenAI, TopHub
- Not tracked in git (use `.env.example` as template)

### Data Flow

```
CLI/API Request
    ↓
TaskManager (load task config)
    ↓
CollectorEngine (fetch news from sources)
    ↓
Extractor (extract content with fallback strategies)
    ↓
Chunker (optional smart chunking)
    ↓
WeaviateClient (vectorize with OpenAI, batch insert)
    ↓
Query/Search (hybrid search with alpha=0.5)
```

### Key Design Patterns

**Task Isolation**: Each task has:
- Separate YAML config file in `config/schedules/`
- Dedicated Weaviate collection (UUID-based naming)
- Independent schedule and status tracking

**Plugin Architecture**:
- Base engine class in `src/engines/base.py`
- Factory pattern in `src/engines/factory.py`
- Easy to add new news sources (RSS, NewsAPI, custom)

**Smart Content Extraction**:
- Multiple strategies with fallback chain
- Early stopping after N successful extractions
- Configurable via `collector.early_stop_threshold`

**Batch Operations**:
- Vectorization and insertion happen in batches
- Dynamic batch sizing with retry logic
- Content length validation before insertion

## Important Implementation Notes

### Weaviate Collection Management

- Always use `TaskManager.get_task().collection_name` to get the collection name
- When deleting tasks, also delete the associated Weaviate collection
- Collection names must start with uppercase letter and contain only alphanumeric + underscore
- The system auto-formats collection names using UUID-based naming

### Schedule System

- Cron format supports minute precision: `minute hour day month day_of_week`
- Example: `35 14 * * *` = Run at 14:35 every day
- Tasks are auto-reloaded every minute, so config changes take effect quickly
- Set `status.enabled: false` to disable a task without deleting it

### Content Processing

- Maximum content length is ~30,000 characters (to stay within 8,191 token limit)
- Content exceeding this limit is skipped during batch insertion (see logs)
- Consider implementing truncation instead of skipping for better coverage
- Chunking is optional and controlled by `weaviate.chunking.enabled` in config

### Search Types

- Current: Pure semantic search using `with_near_text`
- Available: Hybrid search combining semantic + keyword (not currently used)
- Hybrid search alpha parameter: 0=pure keyword, 1=pure semantic, 0.5=balanced

### Frontend Integration

- Frontend is a separate Vite+React+TypeScript app in `frontend/`
- Communicates with backend via REST API on port 8043
- Uses React Router for navigation
- Key pages: TaskList, TaskDetail, Chat, Browse

## Common Development Workflows

### Adding a New Task

1. Use CLI: `python -m src.cli.main task create`
2. Or via API: POST `/api/tasks` with task configuration
3. Task config will be saved to `config/schedules/<task-name>.yaml`
4. Weaviate collection will be auto-created on first run

### Debugging Collection Issues

1. Check Weaviate is running: `docker ps`
2. Check collection exists: Use `python check_data.py` or similar scripts
3. Check logs in `logs/news2context.log`
4. Verify task config has correct `weaviate.collection` value

### Modifying Search Behavior

- Search logic is in `src/storage/weaviate_client.py`
- Methods: `search_news()` (semantic), `hybrid_search()` (semantic+keyword)
- To use hybrid search: Update API routes to call `hybrid_search()` instead
- Adjust `alpha` parameter to balance semantic vs keyword weight

### Running Scheduled Collections

1. Start daemon: `python -m src.cli.main daemon start`
2. Daemon loads all enabled tasks from `config/schedules/`
3. Jobs run according to cron schedule
4. Progress is tracked in task's `status` field
5. Stop daemon: `python -m src.cli.main daemon stop` or Ctrl+C

## File Structure

```
news2context/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── .env                     # API keys (not in git)
│   └── schedules/               # Task configs (*.yaml)
├── src/
│   ├── api/                     # FastAPI REST API
│   │   ├── app.py              # Main app entry
│   │   ├── models.py           # Pydantic models
│   │   └── routes/             # API endpoints
│   ├── cli/                     # CLI commands
│   │   ├── main.py             # CLI entry point
│   │   └── commands/           # Command implementations
│   ├── core/                    # Core business logic
│   │   ├── collector.py        # News collection orchestrator
│   │   ├── task_manager.py     # Task CRUD operations
│   │   ├── source_selector.py  # AI-based source recommendation
│   │   └── scene_analyzer.py   # User scenario analysis
│   ├── engines/                 # News source engines
│   │   ├── base.py             # Abstract base class
│   │   ├── factory.py          # Engine factory
│   │   └── tophub_engine.py    # TopHub implementation
│   ├── scheduler/               # Background scheduling
│   │   ├── daemon.py           # Scheduler daemon
│   │   └── jobs.py             # Job definitions
│   ├── storage/                 # Data persistence
│   │   └── weaviate_client.py  # Weaviate operations
│   └── utils/                   # Utilities
│       ├── config.py           # Config loader
│       ├── logger.py           # Logging setup
│       ├── chunker.py          # Smart text chunking
│       └── markdown_parser.py  # Markdown processing
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── pages/              # Page components
│   │   ├── components/         # Reusable components
│   │   └── App.tsx             # Main app
│   └── package.json
├── logs/                        # Log files
├── data/                        # Data files and cache
├── docker-compose.yml           # Weaviate setup
└── requirements.txt             # Python dependencies
```

## Configuration Values

### Default LLM Settings
- Model: `aws-claude-haiku-4.5`
- Base URL: `https://litellm.futurx.cc`
- Provider: `openai` (API-compatible)
- Max tokens: 2000

### Default Embedding Settings
- Model: `text-embedding-3-small` (in config.yaml) or `text-embedding-3-large` (in schema)
- Dimensions: 1536 (small) or 3072 (large)
- Base URL: `https://litellm.futurx.cc`

### Default Collector Settings
- Max news per source: 15
- Early stop threshold: 3
- Max concurrent requests: 3
- Timeout: 60 seconds

### Default Weaviate Settings
- URL: `http://localhost:8080`
- Batch size: 5 (chunks) or 20 (articles)
- Search type: hybrid
- Hybrid alpha: 0.5
- Similarity threshold: 0.3
- Max results: 5

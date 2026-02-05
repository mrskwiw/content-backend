# CLAUDE.md - Technical Implementation Guide

## Project Overview

Agent implementation for 30-Day Content Jumpstart - AI content generator using Claude 3.5 Sonnet. Business templates are in parent directory (`../templates/`).

## Development Workflow

**Repository Structure:**
- This is the development machine; remote repo is deployment-only
- Exclude: *.md (except README), docs, reports, analysis files, data/outputs/*
- Include: src/, backend/, operator-dashboard/src/, tests/, config files, Docker files

## Development Commands

**Windows paths:** Use backslashes (`\\`) and quotes for spaces. Example: `cd "C:\\path\\with spaces"`

### Setup
```bash
python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
cp .env.example .env  # Set ANTHROPIC_API_KEY
```

### Running
```bash
# Recommended CLI
python run_jumpstart.py tests/fixtures/sample_brief.txt
python run_jumpstart.py --interactive  # Brief builder
python run_jumpstart.py brief.txt --template-quantities '{"1": 3, "2": 5, "9": 2}'

# Backend API
uvicorn backend.main:app --reload --port 8000  # http://localhost:8000/docs

# Dashboard
cd operator-dashboard && npm install && npm run dev  # http://localhost:5173

# Interactive Agent
python agent_cli_enhanced.py chat
```

### Testing & Quality
```bash
pytest                           # All tests (3,077 tests, 95% coverage)
pytest tests/unit/               # Unit only
pytest --cov=src --cov=backend --cov-report=html --cov-report=term  # With detailed coverage
pytest -q                        # Quick run without verbose output
black src/ tests/ && ruff check src/ tests/ && mypy src/  # All quality checks
```

**View coverage report:** Open `htmlcov/index.html` in browser after running coverage tests

### Docker Deployment
```bash
docker-compose up -d api  # Frontend + backend at http://localhost:8000
```

## Architecture

### Agent Pipeline
```
BriefParserAgent → ClientClassifier → TemplateLoader → ContentGeneratorAgent → QAAgent → OutputFormatter
```

**Key behaviors:**
- Async parallel generation (5 concurrent, ~60s for 30 posts)
- 5 validators: hooks, CTAs, length, headlines, keywords (target 85-90%)
- Template selection by client type (B2B_SAAS, AGENCY, COACH, CREATOR)
- Automatic retry (3 attempts with exponential backoff)

### File Organization
```
src/agents/       # 14 AI agents
src/models/       # Pydantic models
src/validators/   # 5 QA validators
src/utils/        # Utilities (anthropic_client, logger)
src/config/       # Settings, template rules

backend/routers/  # API endpoints (/auth, /clients, /projects, /briefs, /generator, /posts)
backend/services/ # Business logic (generator, crud, export, research, trends)
backend/models/   # SQLAlchemy models

operator-dashboard/src/  # React + TypeScript UI

agent/            # Interactive agent (core_enhanced.py, tools.py - 58 tools)

# Parent directory (../)
../templates/     # Business templates (client brief, post library, checklists)
../docs/          # Documentation and archives
```

### API Routes
- `/api/auth/*` - JWT auth
- `/api/clients/*`, `/api/projects/*`, `/api/briefs/*` - CRUD
- `/api/generator/*` - Content generation
- `/api/posts/*` - Post management + QA
- `/api/trends/*` - Google Trends (30/hour rate limit)
- `/api/research/*` - AI research agents

## Configuration

**Environment (`.env`):**
- `ANTHROPIC_API_KEY` (required)
- `ANTHROPIC_MODEL` (default: claude-3-5-sonnet-latest)
- `PARALLEL_GENERATION` (True)
- `MAX_CONCURRENT_API_CALLS` (5)
- `DEBUG_MODE`, `LOG_LEVEL`

**Temperature:** 0.3 for parsing, 0.7 for generation.

## Implementation Details

**Token Optimization:** ~15.5K tokens/client ($0.40-0.60). Context filtering excludes empty fields, limits lists to 5 items, caches system prompt.

**Rate Limiting:** Semaphore limits 5 concurrent requests. Reduce `MAX_CONCURRENT_API_CALLS` if hitting limits.

**UTF-8 (Windows):** Lines 13-15 of 03_post_generator.py force UTF-8 - never remove.

**Template Paths:** Loaded from `../templates/02_POST_TEMPLATE_LIBRARY.md`.

**Error Recovery:** Failed posts create placeholders to maintain batch count.

## Debugging

```bash
# Enable debug logging
DEBUG_MODE=True LOG_LEVEL=DEBUG

# Check logs
logs/content_jumpstart.log

# Verify templates (loads from ../templates/02_POST_TEMPLATE_LIBRARY.md)
python 03_post_generator.py list-templates  # Should show 15

# Check outputs
data/outputs/{ClientName}/  # deliverable.md, brand_voice.md, qa_report.md
```

**UI debugging:** Walk through all steps, take screenshots, check console errors, verify state changes, read error-context.md files.

## Bug Tracking

Document unresolved bugs in `BUGS.md` with: description, steps to reproduce, expected vs actual, component, severity, status.

UI/UX revisions tracked in `../docs/todo.md`.

## Key Patterns

- **Agent-based design:** Each function is a separate agent
- **Async-first:** Default async, sync for debugging
- **Pydantic validation:** All data models validated
- **Fail gracefully:** Placeholder posts on error
- **Business template separation:** Templates in `../templates/`, never modify

## Known Issues

**Deep-Link Routing:** ~~Dashboard refresh on deep routes returns 404.~~ **FIXED** - SPA routing middleware in backend/main.py now handles deep-links correctly. Works when:
- Running production build from FastAPI (serves operator-dashboard/dist)
- Running Vite dev server (automatic SPA fallback)

If issues persist, ensure the frontend is built (`cd operator-dashboard && npm run build`).

## Recent Fixes (February 2, 2026)

**Template Path Issue:** ~~24 coordinator tests failing with FileNotFoundError.~~ **FIXED**
- Root cause: `.env` file had `TEMPLATE_LIBRARY_PATH=../02_POST_TEMPLATE_LIBRARY.md`
- Solution: Updated to `TEMPLATE_LIBRARY_PATH=02_POST_TEMPLATE_LIBRARY.md`
- Template file exists at `Project/02_POST_TEMPLATE_LIBRARY.md`
- All 25 coordinator tests now pass ✅

**Test Organization:** Agent tests moved to correct locations
- Moved 4 tests from `tests/unit/` to `tests/unit/agents/`
- Improved test directory consistency

**Integration Test Coverage:** Added 67 new router integration tests
- `test_router_research.py` - 20 tests (P0 priority, $300-600 features)
- `test_router_trends.py` - 29 tests (Google Trends integration)
- `test_router_assistant.py` - 18 tests (AI assistant chat)

**Test Suite Status:** 3,077 passing tests, **95% coverage achieved** ✅ (target: 90%)

**Coverage Details:** See `TEST_COVERAGE_ACHIEVED.md` for comprehensive coverage report

## Operator Dashboard

React + TypeScript + Vite + Tailwind + shadcn/ui + React Query + Zustand

```bash
cd operator-dashboard
npm run dev        # Development
npm run build      # Production
npm run lint:fix   # ESLint
npm run typecheck  # TypeScript
```

## Interactive Agent

58 tools: content generation, project/client management, research, Google Trends, backend API wrappers.

**Commands:** `chat`, `sessions`, `pending`, `export`, `search`, `summary`
**In-chat:** `help`, `pending`, `scheduled`, `reset`, `new`, `exit`

**Database:** SQLite `data/agent_sessions.db` (sessions, messages, scheduled_tasks)

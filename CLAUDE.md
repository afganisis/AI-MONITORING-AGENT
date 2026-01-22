# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Monitoring Agent for ZeroELD - an autonomous system that monitors Electronic Logging Device (ELD) compliance errors through the Fortex API and automatically fixes them using browser automation via Playwright.

**Architecture:** Full-stack application with FastAPI backend and React/TypeScript frontend

## Development Commands

### Backend (FastAPI + Python 3.11+)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate SECRET_KEY (first time only)
python generate_secret_key.py

# Run development server (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Linting and formatting
black app/ --check          # Check formatting
black app/                  # Apply formatting
flake8 app/                 # Linting
mypy app/                   # Type checking

# Testing
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest app/tests/test_specific.py  # Run specific test file
```

Backend runs on `http://localhost:8000`, API docs at `/docs`

### Frontend (React + TypeScript + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Run development server (hot reload)
npm run dev

# Build for production
npm run build
npm run preview  # Preview production build

# Linting
npm run lint
```

Frontend runs on `http://localhost:5173`

## Architecture Overview

### Backend Structure (`backend/app/`)

```
app/
├── main.py                    # FastAPI app entry point, CORS, startup/shutdown
├── config.py                  # Environment config using pydantic-settings
├── api/routes/                # REST API endpoints
│   ├── health.py             # Health check endpoint
│   ├── agent.py              # Agent control (start/stop/pause/config)
│   ├── errors.py             # Error CRUD operations
│   ├── fixes.py              # Fix history and approval
│   ├── companies.py          # Company/driver filtering
│   └── websocket.py          # WebSocket real-time updates
├── agent/
│   ├── background_service.py # Main agent polling loop (AgentBackgroundService)
│   └── strategies/           # Fix strategies (one per error type)
│       ├── base.py           # BaseFixStrategy abstract class
│       ├── registry.py       # Strategy registration and lookup
│       └── *.py              # Concrete strategies (7+ error types)
├── database/
│   ├── session.py            # SQLAlchemy async engine and session
│   └── models.py             # ORM models: Error, Fix, AgentConfig, FixRule
├── fortex/
│   ├── client.py             # FortexAPIClient (HTTP client for Fortex API)
│   └── models.py             # Pydantic models for API responses
├── playwright/
│   ├── browser_manager.py    # Browser lifecycle + session persistence
│   └── actions.py            # Reusable browser automation actions
├── services/
│   └── error_classifier.py   # Maps error messages to error keys/severity
└── websocket/
    └── manager.py            # WebSocket connection manager (broadcast events)
```

**Key Backend Components:**

1. **AgentBackgroundService** (`agent/background_service.py`) - Main async loop that:
   - Polls Fortex API every N seconds for new errors
   - Classifies errors using `error_classifier`
   - Executes fix strategies via Playwright
   - Broadcasts WebSocket events
   - Respects `AgentConfig` (polling interval, dry-run mode, approval required)

2. **Fix Strategies** (`agent/strategies/`) - Plugin system for error fixes:
   - Each strategy inherits from `BaseFixStrategy`
   - Implements `can_handle()` and `execute()` methods
   - Registered in `strategy_registry` at startup
   - Uses `BrowserManager` for Playwright automation

3. **BrowserManager** (`playwright/browser_manager.py`) - Manages browser lifecycle:
   - Persistent browser context for session cookies
   - Auto-login to Fortex UI
   - Screenshot capture on errors
   - Headless/headful mode toggle

4. **FortexAPIClient** (`fortex/client.py`) - HTTP client for Fortex API:
   - Hardcoded authorization token in headers
   - Redis-backed caching (10min server-side)
   - Automatic retry on network errors
   - Pydantic model validation

### Frontend Structure (`frontend/src/`)

```
src/
├── App.tsx                   # Router setup (BrowserRouter)
├── main.tsx                  # React entry point
├── components/
│   ├── layout/Layout.tsx     # Main layout with sidebar navigation
│   └── common/               # Reusable UI components
│       ├── Card.tsx
│       ├── Button.tsx
│       ├── Badge.tsx
│       ├── AIStatusIndicator.tsx
│       ├── MetricCard.tsx
│       └── ProgressRing.tsx
└── pages/
    ├── Control/Control.tsx   # Main control panel (agent start/stop/config)
    ├── Activity/Activity.tsx # Activity log and error list
    ├── Companies/            # Company/driver selection
    ├── Dashboard/            # Dashboard with stats and charts
    └── Errors/ErrorList.tsx  # Error list with filters
```

**Frontend Tech Stack:**
- React 18 with React Router for navigation
- TypeScript for type safety
- Tailwind CSS for styling
- Zustand for state management (if used)
- Axios for API calls
- Recharts for data visualization

## Database Models (PostgreSQL)

**Core Tables:**

1. **errors** - Error records discovered by agent
   - `error_key` - Error type identifier (e.g., `"diagnosticEvent"`)
   - `severity` - critical/high/medium/low
   - `status` - pending/in_progress/fixed/failed/ignored
   - Relations: one-to-many with `fixes`

2. **fixes** - Fix attempts and results
   - `strategy_name` - Which strategy was used
   - `status` - pending/approved/running/completed/failed
   - `requires_approval` - Boolean flag
   - `execution_time_ms` - Performance tracking

3. **agent_config** - Agent state and configuration (singleton table)
   - `state` - stopped/starting/running/paused/stopping
   - `polling_interval_seconds` - How often to check for errors
   - `max_concurrent_fixes` - Concurrency limit
   - `require_approval` - Auto-fix vs manual approval
   - `dry_run_mode` - Test mode (no actual fixes)

4. **fix_rules** - Per-error-type configuration
   - `error_key` - Links to error type
   - `enabled` - Can this error type be fixed?
   - `auto_fix` - Fix without approval?
   - `priority` - 0-100 (higher = more urgent)

## Fortex API Integration

**API Type:** Custom REST API (not PostgREST, despite ZeroELD heritage)

**Base URL:** `https://api.fortex-zero.us` (configurable via `FORTEX_API_URL`)

**Authentication:** Hardcoded token in `Authorization` header (value: `y3He9C57ecfmMAsR19`)

**Key Endpoints:**

- `GET /health` - Health check
- `GET /monitoring` - Overview with error counts and driver stats
- `GET /monitoring/companies` - List of companies with error summaries
- `GET /monitoring/logs-with-errors` - Paginated error list with filtering
- `POST /monitoring/smart-analyze` - AI-powered error analysis

**Important:** Fortex API has Redis caching (10 minute TTL) server-side. Don't over-poll.

## Playwright Browser Automation

**Login Flow:**
1. BrowserManager loads persistent session from `./playwright_data/session_state.json`
2. If no session, navigates to `FORTEX_UI_URL` and performs login
3. Session cookies saved for future runs

**Fix Execution Pattern:**
1. Strategy receives `browser_manager.page` (Playwright Page object)
2. Navigate to error location in UI
3. Perform fix actions (clicks, fills, etc.)
4. Capture screenshot on error
5. Return `FixResult` with success status

**Configuration:**
- `PLAYWRIGHT_HEADLESS=true` - Run without visible browser
- `PLAYWRIGHT_SCREENSHOTS_DIR=./screenshots` - Error screenshots
- `PLAYWRIGHT_SESSION_DIR=./playwright_data` - Session persistence

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Generate with `python backend/generate_secret_key.py`
- `FORTEX_UI_USERNAME` / `FORTEX_UI_PASSWORD` - Credentials for browser automation

**Optional but Important:**
- `AGENT_DRY_RUN_MODE=true` - Test mode (no actual fixes applied)
- `AGENT_REQUIRE_APPROVAL=false` - Auto-fix without human approval
- `PLAYWRIGHT_HEADLESS=false` - Show browser for debugging

## Agent Lifecycle

1. **Startup**: API starts, database tables created, agent initialized but NOT running
2. **Manual Start**: User calls `POST /api/agent/start` to begin polling
3. **Polling Loop**: Every N seconds:
   - Fetch errors from Fortex API
   - Classify new errors, save to database
   - Load pending fixes
   - Execute fix strategies via Playwright
   - Broadcast WebSocket updates
4. **Pause/Stop**: User controls via API or frontend
5. **Shutdown**: Graceful cleanup on SIGTERM/SIGINT

## Error Classification System

**Error Classifier** (`services/error_classifier.py`) maps error messages to structured data:

```python
{
  "error_key": "diagnosticEvent",        # Unique identifier
  "error_name": "Diagnostic Event",      # Human-readable name
  "severity": "low",                     # critical/high/medium/low
  "category": "diagnostic"               # Category grouping
}
```

**Severity Levels:**
- **critical** - Data integrity violations (sequential ID breaks)
- **high** - Location/odometer errors, status placement errors
- **medium** - Missing events, unidentified drivers
- **low** - Diagnostic events, power-up/shutdown warnings

## Working with Fix Strategies

To add a new fix strategy:

1. Create `backend/app/agent/strategies/my_error.py`
2. Inherit from `BaseFixStrategy`
3. Implement required methods:
   ```python
   class MyErrorStrategy(BaseFixStrategy):
       @property
       def error_key(self) -> str:
           return "myErrorKey"

       @property
       def strategy_name(self) -> str:
           return "My Error Fix Strategy"

       async def can_handle(self, error) -> bool:
           return error.error_key == self.error_key

       async def execute(self, error, fix, browser_manager) -> FixResult:
           # Use browser_manager.page for automation
           page = browser_manager.page
           # ... perform fix actions ...
           return FixResult(success=True, message="Fixed", execution_time_ms=1000)
   ```
4. Register in `strategies/registry.py` by importing and adding to registry

## WebSocket Events

Frontend can connect to `ws://localhost:8000/ws` for real-time updates:

**Event Types:**
- `agent_status` - Agent state changed (running/stopped/paused)
- `error_discovered` - New error found
- `fix_started` - Fix execution began
- `fix_completed` - Fix finished (success/failure)
- `fix_approved` / `fix_rejected` - Manual approval events

## Legacy Notes

This project originally integrated with ZeroELD's PostgREST API (`https://cloud.zeroeld.us`). The architecture was refactored to use Fortex API, but some references remain:
- `ZEROELD_*` environment variables (unused, kept for reference)
- `zeroVios.js` - Error filter definitions (now replaced by Python classifier)
- PostgREST documentation in original `CLAUDE.md` (still relevant for understanding ELD domain)

The ELD domain concepts (duty statuses, HOS compliance, event types) still apply - only the API changed.

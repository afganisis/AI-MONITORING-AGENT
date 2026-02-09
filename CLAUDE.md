# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Monitoring Agent for ZeroELD/Fortex** - Autonomous system that monitors Electronic Logging Device (ELD) compliance errors through the Fortex API and automatically fixes them using browser automation via Playwright.

### Architecture
- **Backend:** FastAPI + Python 3.11+ + PostgreSQL (Supabase) + Playwright
- **Frontend:** React 18 + TypeScript + Tailwind CSS (cyberpunk theme) + Vite
- **API Integration:** Fortex REST API (with Redis caching on their side)
- **Browser Automation:** Playwright (async, visible browser mode by default)
- **Database:** PostgreSQL via Supabase with data enrichment layer

### Current Status
- **Phase 1 Complete:** Demo agent workflow (login → company selection → driver selection → log extraction → Smart Analyze)
- **Data Enrichment:** Driver/company name lookup from Supabase
- **API Endpoints:** Full REST API with WebSocket support
- **Phase 2 (In Progress):** Automatic error correction using fix strategies
- **Phase 3 (Future):** Production deployment and monitoring

### Project Structure
```
AI MONITORING/
├── backend/                    # FastAPI + Python 3.11+
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Environment configuration
│   │   ├── api/routes/        # REST API endpoints
│   │   ├── agent/             # Background service + fix strategies
│   │   ├── database/          # SQLAlchemy ORM models
│   │   ├── fortex/            # Fortex API client
│   │   ├── supabase/          # Supabase client for enrichment
│   │   ├── playwright/        # Browser automation
│   │   ├── services/          # Business logic services
│   │   └── websocket/         # WebSocket manager
│   ├── test_demo_agent.py     # Main demo script
│   └── requirements.txt
│
├── frontend/                   # React 18 + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── contexts/          # AuthContext, DataContext
│   │   ├── pages/             # Control, Activity, Results
│   │   └── utils/             # Helper functions
│   └── package.json
│
└── CLAUDE.md                   # This file
```

---

## Quick Start

### Requirements
- Python 3.11+ (3.13+ requires `winloop` on Windows)
- Node.js 18+
- PostgreSQL 15+ (or Supabase)
- Fortex API credentials

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Generate SECRET_KEY
python generate_secret_key.py

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend URLs:**
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

**Frontend URL:** `http://localhost:5173`

### Run Demo Agent

```bash
cd backend
python test_demo_agent.py
```

---

## Key Architecture Patterns

### Backend Service Organization
- **API Layer** (`app/api/routes/`) - FastAPI endpoints with dependency injection
- **Service Layer** (`app/services/`) - Business logic (error_classifier, auth_service, log_scanner_service, progress_tracker)
- **Agent System** (`app/agent/`) - Background service + strategy registry pattern for error fixes
- **Data Access** (`app/database/`) - SQLAlchemy 2.0 async ORM models
- **External APIs** (`app/fortex/`, `app/supabase/`) - Client wrappers for external services
- **Automation** (`app/playwright/`) - Browser automation manager and reusable actions

### Data Enrichment System
**Critical Pattern:** The system stores only IDs in the database, then enriches with names from Supabase at query time.

```python
# Database stores: driver_id, company_id (UUIDs)
# API enriches with: driver_name, company_name (from Supabase lookup)
# Frontend receives: Complete objects with human-readable names
```

**Files involved:**
- `backend/app/supabase/client.py` - Supabase queries for drivers/companies
- `backend/app/api/routes/agent.py` - Enrichment logic in `/results` endpoint
- `backend/app/services/scanner_service.py` - Saves enriched names during scan

### Frontend Architecture
- **React Router** - 3 main pages: Control, Activity, Results
- **Context API** - AuthContext (JWT auth) + DataContext (global state with caching)
- **Tailwind CSS** - Custom cyberpunk theme with neon accents
- **Real-time Updates** - WebSocket integration for agent status

### Database Schema
```
┌─────────────┐     ┌─────────────┐
│   errors    │────<│    fixes    │
├─────────────┤     ├─────────────┤
│ id (UUID)   │     │ id (UUID)   │
│ driver_id   │     │ error_id    │
│ driver_name │     │ strategy    │
│ company_id  │     │ status      │
│ company_name│     │ result_msg  │
│ error_key   │     │ exec_time   │
│ error_name  │     │ created_at  │
│ severity    │     └─────────────┘
│ status      │
│ discovered_at│
└─────────────┘

┌─────────────────┐   ┌─────────────┐
│  agent_config   │   │  fix_rules  │
├─────────────────┤   ├─────────────┤
│ state           │   │ error_key   │
│ polling_interval│   │ enabled     │
│ max_concurrent  │   │ auto_fix    │
│ require_approval│   │ priority    │
│ dry_run_mode    │   └─────────────┘
└─────────────────┘
```

---

## Error Classification System

**23 error types** classified by severity with auto-detection:

### LOW Severity (7 types) - Auto-fixable
| Key | Name | Pattern |
|-----|------|---------|
| `diagnosticEvent` | Diagnostic Event | `diagnostic` |
| `noShutdownError` | No Shutdown | `shutdown`, `no shut` |
| `noPowerUpError` | No Power-Up | `power-up`, `power up` |
| `excessiveLogInWarning` | Excessive Login | `excessive.*log.*in` |
| `excessiveLogOutWarning` | Excessive Logout | `excessive.*log.*out` |
| `eventHasManualLocation` | Manual Location | `manual.*location` |
| `eventIsNotDownloaded` | Not Downloaded | `not downloaded` |

### MEDIUM Severity (8 types)
| Key | Name |
|-----|------|
| `driverNotAssigned` | Driver Not Assigned |
| `dutyStatusMismatch` | Duty Status Mismatch |
| `invalidDutyStatus` | Invalid Duty Status |
| `dutyStatusConflict` | Duty Status Conflict |
| `timingGap` | Timing Gap |
| `falseAutoEvent` | False Auto Event |
| `locationMismatch` | Location Mismatch |
| `missingRequiredAnnotation` | Missing Annotation |

### HIGH Severity (6 types)
| Key | Name |
|-----|------|
| `unresolvedAnnotation` | Unresolved Annotation |
| `unresolvedDriverEdit` | Unresolved Driver Edit |
| `hosViolation14Hour` | HOS Violation 14-Hour |
| `hosViolation8Hour` | HOS Violation 8-Hour |
| `hosViolation11Hour` | HOS Violation 11-Hour |
| `hosViolation70Hour` | HOS Violation 70-Hour |

### CRITICAL Severity (2 types)
| Key | Name |
|-----|------|
| `dataMismatchForTransfer` | Data Mismatch for Transfer |
| `unidentifiedDrivingEvent` | Unidentified Driving Event |

**Classifier:** `backend/app/services/error_classifier.py`

---

## API Endpoints

### Agent Control
```
GET  /api/agent/status           # Get agent state and config
POST /api/agent/start            # Start agent
POST /api/agent/stop             # Stop agent
POST /api/agent/pause            # Pause agent
PATCH /api/agent/config          # Update config
POST /api/agent/scan-logs        # Trigger log scan
GET  /api/agent/scan/{id}/progress  # Get scan progress
GET  /api/agent/results          # Get scan results
```

### Errors
```
GET  /api/errors                 # List errors (paginated)
GET  /api/errors/stats           # Error statistics (optimized SQL)
GET  /api/errors/by-driver       # Errors grouped by driver
GET  /api/errors/{id}            # Get error by ID
PATCH /api/errors/{id}/status    # Update error status
DELETE /api/errors/{id}          # Delete error
POST /api/errors/refresh-names   # Refresh names from Supabase
```

### Fixes
```
GET  /api/fixes                  # List fixes (paginated)
GET  /api/fixes/pending-approvals # Fixes awaiting approval
GET  /api/fixes/stats/summary    # Fix statistics
GET  /api/fixes/{id}             # Get fix by ID
POST /api/fixes/{id}/approve     # Approve fix
POST /api/fixes/{id}/reject      # Reject fix
```

### Companies
```
GET  /api/companies              # List companies with drivers
```

---

## Playwright Browser Automation

### Critical Patterns

**Ant Design Select Components (keyboard navigation required):**
```python
# Direct .click() on options DOES NOT WORK with Ant Design
# Must use keyboard navigation:
await page.click('.ant-select')
await page.keyboard.press('ArrowDown')
await page.keyboard.press('Enter')
```

**New Tab Handling:**
```python
# CREATE button opens new tab - must capture it
async with page.context.expect_page() as new_page_info:
    await create_button.click()
new_page = await new_page_info.value
page = new_page  # Switch context to new tab
```

**Coordinate-Based Clicks (fallback for stubborn buttons):**
```python
# When React event handlers fail, use raw coordinates
box = await button.bounding_box()
await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
```

**Date Handling:**
```python
# Ant Design DatePicker uses ISO format YYYY-MM-DD internally
start_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")
```

### Demo Agent Workflow (`test_demo_agent.py`)

1. **Login** → Fill `#basic_username`, `#basic_password`, submit
2. **Smart Analyze API** → GET `/monitoring/companies` to prioritize companies with errors
3. **Select Company** → Choose company with highest error count
4. **Select Driver** → Keyboard navigation through Ant Design Select
5. **CREATE** → Click button, capture new tab with `expect_page()`
6. **Date Range** → Set to last 9 days (today - 8 days)
7. **LOAD** → Coordinate-based click on LOAD button
8. **Scroll & Extract** → 15 scroll iterations to load lazy-loaded table data
9. **Basic Analysis** → Pattern match on `status` and `notes` columns
10. **Smart Analyze** → POST `/monitoring/smart-analyze` with driver_id + date range
11. **Save Results** → JSON files to `logs_data/`, screenshots to `screenshots/`

---

## Fortex API Integration

**Base URL:** `https://api.fortex-zero.us`
**Auth:** Token in `Authorization: Bearer <token>` header
**System:** `system=zero` query param required on all requests
**Caching:** Redis caching on Fortex side (10 min TTL) - avoid excessive polling

**Key Endpoints:**
```
GET  /monitoring/companies              # List companies with error counts
GET  /monitoring/logs-with-errors       # Paginated error list
POST /monitoring/smart-analyze          # AI error analysis
     Body: { "driverId": "uuid", "dateFrom": "YYYY-MM-DD", "dateTo": "YYYY-MM-DD" }
```

**Client:** `app/fortex/client.py` (FortexAPIClient) wraps httpx with retry logic

---

## Environment Configuration

### Required Variables
```bash
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Supabase (for driver/company name enrichment)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<anon_key>
SUPABASE_SERVICE_KEY=<service_key>

# Security
SECRET_KEY=<generate with generate_secret_key.py>

# Fortex API
FORTEX_API_URL=https://api.fortex-zero.us
FORTEX_AUTH_TOKEN=<token>
FORTEX_SYSTEM_NAME=zero

# Fortex UI (Playwright)
FORTEX_UI_URL=https://fortex-zero.us/
FORTEX_UI_USERNAME=<username>
FORTEX_UI_PASSWORD=<password>
```

### Optional Variables (with defaults)
```bash
PLAYWRIGHT_HEADLESS=false              # Show browser (useful for debugging)
PLAYWRIGHT_SCREENSHOTS_DIR=./screenshots
AGENT_DRY_RUN_MODE=false
AGENT_REQUIRE_APPROVAL=true
AGENT_POLLING_INTERVAL_SECONDS=300
```

---

## Troubleshooting

### Playwright Issues

| Problem | Solution |
|---------|----------|
| Login fails or hangs | Set `PLAYWRIGHT_HEADLESS=false`, verify credentials |
| Driver selection doesn't work | Use keyboard navigation: `ArrowDown` + `Enter` |
| LOAD button not found after CREATE | Use `page.context.expect_page()` to capture new tab |
| Browser doesn't open | Check `PLAYWRIGHT_HEADLESS=false` in `.env` |
| Chrome notifications appear | Clear `./playwright_data` directory |

### Python 3.13+ on Windows
Playwright has event loop issues with Python 3.13+:
```bash
pip install winloop
```
Code auto-detects and uses winloop if available (see `app/main.py`)

### API Issues

| Problem | Solution |
|---------|----------|
| GET /api/agent/results returns 500 | Fixed: use `discovered_at` not `detected_at` |
| Missing driver_name/company_name | Verify Supabase credentials in `.env` |
| 401 Unauthorized from Fortex API | Check `FORTEX_AUTH_TOKEN` validity |

### Database Issues
```bash
# Verify DATABASE_URL format
postgresql+asyncpg://user:password@host:port/database

# For Supabase, use pooler connection string with :6543 port
```

---

## Code Conventions

### Async/Await
- All I/O operations must be async (database, HTTP, Playwright)
- Use `async with` for context managers
- Never use blocking operations in async functions

### Logging
```python
from loguru import logger

logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception with traceback")
logger.debug("Debug message")
```
- Never use `print()` statements

### Type Hints
- All function signatures must have type hints
- Use `Optional[T]` for nullable types
- Pydantic models for API request/response validation

### Error Handling
- Wrap Playwright operations in try/except
- Take screenshots on errors: `page.screenshot(path=f"{screenshot_dir}/error.png")`
- Log full exception context with `logger.exception()`

### Database Field Names
- Use `discovered_at` (NOT `detected_at`) for error discovery timestamp
- UUID fields: `driver_id`, `company_id`, `error_id`
- Status field uses string enums: `"pending"`, `"in_progress"`, `"fixed"`, `"failed"`

### SQL Optimization
- Use SQL GROUP BY for aggregations, not Python loops
- Use CASE expressions for conditional counts
- Example pattern (used in `/errors/stats`):
```python
status_result = await db.execute(
    select(Error.status, func.count(Error.id))
    .group_by(Error.status)
)
by_status = {row[0]: row[1] for row in status_result.all()}
```

---

## Roadmap

### Phase 2: Automatic Error Correction (In Progress)
- Implement fix strategies for LOW severity errors
- Integrate AgentBackgroundService with polling
- Add approval workflow for fixes
- Fix success/failure tracking

### Phase 3: Production Dashboard
- Real-time WebSocket updates
- Error list with filters and search
- Fix history timeline
- Agent control panel (start/stop/pause)

### Phase 4: Production Ready
- Comprehensive test coverage
- Database migrations (Alembic)
- Docker containers
- CI/CD pipeline

---

*Last updated: 2026-02-05*
*Phase 1 complete. Data enrichment working. SQL optimizations applied.*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Monitoring Agent for ZeroELD/Fortex** - Autonomous system that monitors Electronic Logging Device (ELD) compliance errors through the Fortex API and automatically fixes them using browser automation via Playwright.

### Architecture
- **Backend:** FastAPI + Python 3.11+ + PostgreSQL + Playwright
- **Frontend:** React 18 + TypeScript + Tailwind CSS + Vite
- **API Integration:** Fortex REST API (with Redis caching)
- **Browser Automation:** Playwright (async)

### Current Status
✅ **Phase 1 Complete:** Demo agent that logs in, selects companies/drivers with errors, extracts logs, and performs Smart Analyze
⏸️ **Phase 2 (Next):** Automatic error correction using fix strategies
⏸️ **Phase 3 (Future):** Frontend dashboard with real-time WebSocket updates

---

## Quick Start

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Generate SECRET_KEY (first time)
python generate_secret_key.py

# Copy and configure .env
cp .env.example .env
# Edit .env with your Fortex credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on `http://localhost:8000`, API docs at `/docs`

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

Frontend runs on `http://localhost:5173`

### Run Demo Agent

```bash
cd backend
python test_demo_agent.py
```

This will:
1. Login to Fortex UI
2. Call Smart Analyze API to find companies with errors
3. Select company with most errors
4. Select first driver
5. Extract last 9 days of logs
6. Analyze for compliance issues
7. Save results to `logs_data/`

---

## Project Structure

```
AI MONITORING/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Environment configuration
│   │   ├── api/routes/        # REST API endpoints
│   │   ├── agent/
│   │   │   ├── background_service.py  # Main agent loop
│   │   │   └── strategies/            # Fix strategies (one per error type)
│   │   ├── database/
│   │   │   ├── session.py     # SQLAlchemy async engine
│   │   │   └── models.py      # ORM models
│   │   ├── fortex/
│   │   │   ├── client.py      # FortexAPIClient (HTTP client)
│   │   │   └── models.py      # Pydantic models
│   │   ├── playwright/
│   │   │   ├── browser_manager.py  # Browser lifecycle
│   │   │   └── actions.py          # Reusable browser actions
│   │   ├── services/
│   │   │   └── error_classifier.py # Error classification
│   │   └── websocket/
│   │       └── manager.py     # WebSocket manager
│   ├── test_demo_agent.py     # **Main demo script**
│   ├── generate_secret_key.py # Secret key generator
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment template
│
├── frontend/                  # React application
│   ├── src/
│   │   ├── App.tsx           # Router setup
│   │   ├── components/       # UI components
│   │   └── pages/            # Page components
│   └── package.json
│
├── CLAUDE.md                  # **This file**
├── AGENT_DEMO_SUMMARY.md      # Detailed demo notes
└── README.md                  # Project overview
```

---

## Demo Agent Workflow (`backend/test_demo_agent.py`)

### Flow
1. **Login** → Authenticate to Fortex UI
2. **Smart Analyze (Company Level)** → Call `/monitoring/companies` to find companies with errors
3. **Select Company** → Auto-select company with highest error count
4. **Select Driver** → Use keyboard navigation for Ant Design Select
5. **CREATE** → Opens new browser tab
6. **Date Selection** → Last 9 days (today - 8 days)
7. **LOAD** → Load logs
8. **Extract Logs** → Scroll and extract all table rows to JSON
9. **Basic Analysis** → Scan for error keywords
10. **Smart Analyze (Driver Level)** → AI-powered error detection
11. **Save Results** → Store logs and analysis

### Critical Technical Details

**New Tab Handling:**
```python
async with page.context.expect_page() as new_page_info:
    await create_button.click()
new_page = await new_page_info.value
page = new_page  # Switch to new tab
```

**Ant Design Select (keyboard navigation required):**
```python
await page.click('.ant-select')
await page.keyboard.press('ArrowDown')
await page.keyboard.press('Enter')
```

**Coordinate-Based Click (for stubborn buttons):**
```python
box = await button.bounding_box()
await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
```

### Data Output
- `logs_data/logs_<driver>_<timestamp>.json` - Raw logs
- `logs_data/issues_<driver>_<timestamp>.json` - Detected issues
- `logs_data/smart_analyze_<driver>_<timestamp>.json` - AI analysis
- `screenshots/<step>.png` - Screenshots at each step

---

## Fortex API Integration

**Base URL:** `https://api.fortex-zero.us`
**Auth:** Token in `Authorization` header (from `.env`)

**Key Endpoints:**
- `GET /monitoring/companies` - List companies with error counts
- `GET /monitoring/logs-with-errors` - Paginated error list
- `POST /monitoring/smart-analyze` - AI error analysis
  ```json
  {
    "driverId": "uuid",
    "dateFrom": "2026-01-19",
    "dateTo": "2026-01-27"
  }
  ```

**Caching:** Fortex has Redis caching (10 min TTL) - don't over-poll.

---

## Database Models

**Tables:**
- `errors` - Error records (error_key, severity, status, driver_id, company_id)
- `fixes` - Fix attempts (strategy_name, status, requires_approval)
- `agent_config` - Agent state (singleton: state, polling_interval, require_approval)
- `fix_rules` - Per-error config (error_key, enabled, auto_fix, priority)

---

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aiagent
SECRET_KEY=<generate with generate_secret_key.py>
FORTEX_API_URL=https://api.fortex-zero.us
FORTEX_API_TOKEN=y3He9C57ecfmMAsR19
FORTEX_UI_URL=https://fortex-zero.us
FORTEX_UI_USERNAME=<your_username>
FORTEX_UI_PASSWORD=<your_password>
```

### Optional
```bash
AGENT_DRY_RUN_MODE=false
AGENT_REQUIRE_APPROVAL=true
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_SCREENSHOTS_DIR=./screenshots
```

---

## Common Tasks

### Start Dev Environment
```bash
# Backend
cd backend && venv\Scripts\activate && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Run Demo
```bash
cd backend && python test_demo_agent.py
```

### Linting
```bash
cd backend
black app/
flake8 app/
mypy app/
```

---

## Troubleshooting

### Playwright Login Fails
- Check `FORTEX_UI_URL` and credentials in `.env`
- Run with `PLAYWRIGHT_HEADLESS=false` to see browser

### Driver Selection Not Working
- Use keyboard navigation (Ant Design issue)

### LOAD Button Not Found
- Check if CREATE opens new tab - use `expect_page()`

### Smart Analyze Returns 401
- Check `FORTEX_API_TOKEN` in `.env`

---

## Next Steps (Roadmap)

### Phase 2: Auto Error Correction
- [ ] Implement fix strategies for top error types
- [ ] Integrate AgentBackgroundService
- [ ] Add approval workflow

### Phase 3: Frontend Dashboard
- [ ] Real-time WebSocket updates
- [ ] Error list with filters
- [ ] Agent control panel

---

## Best Practices

- Use `async`/`await` for all I/O
- Type hints for function signatures
- `loguru` for logging (not `print()`)
- Wrap Playwright in `try`/`except`
- Take screenshots on errors
- Use Pydantic for API validation

---

## Key Learnings

1. **Ant Design Select requires keyboard navigation** - `.click()` on options doesn't work
2. **Fortex CREATE opens new tab** - Must use `expect_page()`
3. **Date variables must be function-scoped** - Multiple steps use same dates
4. **Coordinate-based clicks are most reliable** - When React handlers fail
5. **Smart Analyze should run BEFORE company selection** - Prioritize companies with errors

---

*Last updated: 2026-01-27*
*Demo agent fully functional. Next: Fix strategy implementation.*

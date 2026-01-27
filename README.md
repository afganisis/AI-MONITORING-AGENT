# AI Monitoring Agent для ZeroELD/Fortex

Интеллектуальная система автоматического мониторинга и исправления ошибок ELD (Electronic Logging Device) compliance через Fortex API с использованием browser automation.

## 🎯 Возможности

- **Smart Analyze** - AI-powered анализ логов для обнаружения ошибок compliance
- **Автоматический выбор** - приоритизация компаний и драйверов с ошибками
- **Browser Automation** - Playwright для взаимодействия с Fortex UI
- **Extraction & Analysis** - извлечение логов и их анализ
- **Real-time Monitoring** - непрерывное сканирование и мониторинг (в разработке)
- **Dashboard** - визуализация статистики и результатов (в разработке)

## ✅ Текущий статус

**Phase 1 (COMPLETE):** Demo Agent - полный цикл от логина до анализа
**Phase 2 (Next):** Automatic Error Correction - исправление ошибок с помощью fix strategies
**Phase 3 (Future):** Production Dashboard - WebSocket updates, real-time monitoring

## 🏗️ Архитектура

```
AI MONITORING/
├── backend/                    # FastAPI + Python 3.11+
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Environment configuration
│   │   ├── api/routes/        # REST API endpoints
│   │   ├── agent/
│   │   │   ├── background_service.py  # Agent polling loop
│   │   │   └── strategies/            # Fix strategies
│   │   ├── database/          # SQLAlchemy ORM models
│   │   ├── fortex/            # Fortex API client
│   │   ├── playwright/        # Browser automation
│   │   ├── services/          # Error classification
│   │   └── websocket/         # WebSocket manager
│   ├── test_demo_agent.py     # **Main demo script**
│   └── requirements.txt
│
├── frontend/                   # React 18 + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── pages/             # Page components
│   │   └── services/          # API integration
│   └── package.json
│
├── CLAUDE.md                   # Development guide
├── AGENT_DEMO_SUMMARY.md       # Demo implementation notes
└── README.md                   # This file
```

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Fortex API credentials
- Chromium browser (auto-installed by Playwright)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Generate SECRET_KEY
python generate_secret_key.py

# Configure .env file
cp .env.example .env
# Edit .env with your credentials

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

Frontend: `http://localhost:5173`

### 3. Run Demo Agent

```bash
cd backend
python test_demo_agent.py
```

**What it does:**
1. Login to Fortex UI with credentials
2. Call `/monitoring/companies` API to find companies with errors
3. Auto-select company with highest error count
4. Select first driver (using keyboard navigation for Ant Design)
5. Open driver logs in new browser tab
6. Set date range to last 9 days
7. Extract all log entries to JSON
8. Analyze logs for compliance issues
9. Call `/monitoring/smart-analyze` for AI-powered detection
10. Save results to `logs_data/`

**Output:**
- Console logs (color-coded with Loguru)
- `logs_data/logs_<driver>_<timestamp>.json` - Raw extracted logs
- `logs_data/issues_<driver>_<timestamp>.json` - Detected issues
- `logs_data/smart_analyze_<driver>_<timestamp>.json` - AI analysis
- `screenshots/<step>.png` - Screenshots at each step

## 📖 Документация

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive development guide
- **[AGENT_DEMO_SUMMARY.md](AGENT_DEMO_SUMMARY.md)** - Detailed demo implementation notes
- **[backend/SETUP.md](backend/SETUP.md)** - Backend setup instructions
- **API Docs:** `http://localhost:8000/docs` (after starting backend)

## 🔍 Fortex API Integration

**Base URL:** `https://api.fortex-zero.us`

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

**Caching:** Fortex has Redis caching (10 min TTL) - avoid over-polling.

## 🎨 Технологии

### Backend
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Database
- **Playwright** - Browser automation
- **httpx** - Async HTTP client
- **Pydantic** - Data validation
- **Loguru** - Logging

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling with custom cyberpunk theme
- **Vite** - Build tool
- **Recharts** - Data visualization
- **React Router** - Navigation

### Integration
- **Fortex REST API** - ELD compliance monitoring
- **WebSockets** - Real-time updates (WIP)

## 📊 Database Models

**Core Tables:**

- `errors` - Error records
  - Fields: `error_key`, `severity`, `status`, `driver_id`, `company_id`
  - Relations: one-to-many with `fixes`

- `fixes` - Fix attempts
  - Fields: `strategy_name`, `status`, `requires_approval`, `execution_time_ms`

- `agent_config` - Agent state (singleton)
  - Fields: `state`, `polling_interval_seconds`, `require_approval`, `dry_run_mode`

- `fix_rules` - Per-error-type configuration
  - Fields: `error_key`, `enabled`, `auto_fix`, `priority`

## 🛠️ Environment Variables

### Required

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aiagent

# Security
SECRET_KEY=<generate with generate_secret_key.py>

# Fortex API
FORTEX_API_URL=https://api.fortex-zero.us
FORTEX_AUTH_TOKEN=y3He9C57ecfmMAsR19

# Fortex UI (for Playwright)
FORTEX_UI_URL=https://fortex-zero.us
FORTEX_UI_USERNAME=<your_username>
FORTEX_UI_PASSWORD=<your_password>
```

### Optional

```bash
# Agent config
AGENT_DRY_RUN_MODE=false          # Test mode (no actual fixes)
AGENT_REQUIRE_APPROVAL=true       # Manual approval for fixes
AGENT_POLLING_INTERVAL=60         # Seconds between checks

# Playwright
PLAYWRIGHT_HEADLESS=true          # Run without visible browser
PLAYWRIGHT_SCREENSHOTS_DIR=./screenshots
PLAYWRIGHT_SESSION_DIR=./playwright_data
```

## 📝 Demo Agent Workflow

### Step-by-Step Process

1. **Login** → Authenticate to Fortex UI (`#basic_username`, `#basic_password`)
2. **Smart Analyze** → GET `/monitoring/companies` to find errors
3. **Company Selection** → Auto-select company with most errors (or fallback to first)
4. **Driver Selection** → Keyboard navigation (ArrowDown + Enter) for Ant Design Select
5. **CREATE** → Click button, new tab opens automatically
6. **Tab Switch** → Use `page.context.expect_page()` to capture new tab
7. **Date Selection** → Set range to last 9 days (MM/DD/YYYY format)
8. **LOAD** → Coordinate-based click (`page.mouse.click(x, y)`)
9. **Scroll & Extract** → 15 scrolls to load lazy data, extract table rows
10. **Basic Analysis** → Scan `status` and `notes` for error keywords
11. **Smart Analyze** → POST `/monitoring/smart-analyze` for AI detection
12. **Save Results** → JSON files + screenshots

### Technical Details

**Ant Design Workaround (Keyboard Navigation):**
```python
await page.click('.ant-select')
await page.keyboard.press('ArrowDown')
await page.keyboard.press('Enter')
```

**New Tab Handling:**
```python
async with page.context.expect_page() as new_page_info:
    await create_button.click()
new_page = await new_page_info.value
page = new_page  # Switch to new tab
```

**Coordinate-Based Click:**
```python
box = await button.bounding_box()
await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
```

## 🧪 Разработка

### Linting & Formatting

```bash
# Backend
cd backend
black app/               # Format code
flake8 app/              # Lint
mypy app/                # Type check

# Frontend
cd frontend
npm run lint             # ESLint
```

### Testing

```bash
# Backend
cd backend
pytest                   # Run all tests
pytest -v                # Verbose output

# Frontend
cd frontend
npm test                 # Run tests (when configured)
```

### Debug Mode

```bash
# Run Playwright in visible browser mode
# .env
PLAYWRIGHT_HEADLESS=false

# Enable Playwright inspector
PWDEBUG=1 python test_demo_agent.py
```

## 🐛 Troubleshooting

### Playwright Login Fails
- Verify `FORTEX_UI_URL`, `FORTEX_UI_USERNAME`, `FORTEX_UI_PASSWORD` in `.env`
- Run with `PLAYWRIGHT_HEADLESS=false` to see what's happening
- Check if Fortex changed their login page structure

### Driver Selection Not Working
- Ant Design requires keyboard navigation (`.click()` on options doesn't work)
- Solution implemented: `ArrowDown` + `Enter`

### LOAD Button Not Found
- CREATE opens new tab - must use `expect_page()` to capture it
- Coordinate-based click implemented as fallback

### Smart Analyze Returns 401
- Check `FORTEX_AUTH_TOKEN` in `.env`
- Verify token is still valid

### Database Connection Error
```bash
# Create database
createdb aiagent

# Verify connection string format
postgresql+asyncpg://user:password@host:port/database
```

## 🗺️ Roadmap

### Phase 2: Automatic Error Correction (Next)
- [ ] Implement fix strategies for top 5 error types
- [ ] Integrate AgentBackgroundService with polling
- [ ] Add approval workflow for fixes
- [ ] Fix success/failure tracking

### Phase 3: Production Dashboard
- [ ] Real-time WebSocket updates
- [ ] Error list with filters and search
- [ ] Fix history timeline
- [ ] Agent control panel (start/stop/pause)
- [ ] Company/driver drill-down views

### Phase 4: Production Ready
- [ ] Comprehensive test coverage
- [ ] Database migrations (Alembic)
- [ ] Docker containers
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting

## 🔐 Безопасность

- JWT authentication for Fortex API
- `SECRET_KEY` for internal security
- CORS configuration
- Audit log for all agent actions
- Dry-run mode for safe testing
- Approval workflow for critical fixes

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📞 Support

- **Issues:** Report bugs at GitHub Issues
- **Documentation:** See `CLAUDE.md` for development guide
- **API Docs:** `http://localhost:8000/docs` when backend is running

## 📄 License

This project is private and proprietary.

---

**Last Updated:** 2026-01-27
**Status:** Phase 1 Complete ✅ | Phase 2 In Progress 🚧
**Demo:** Fully functional end-to-end workflow

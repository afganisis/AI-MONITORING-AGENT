# Critical Fixes Required - Backend

## Overview
3 critical issues found that MUST be fixed before deployment.

---

## CRITICAL ISSUE #1: Attribute Name Mismatch

**File:** `backend/test_demo_agent.py`
**Lines:** 146, 884
**Current Code:**
```python
"Authorization": settings.fortex_api_token
```

**Fixed Code:**
```python
"Authorization": settings.fortex_auth_token
```

**Why:** The config file defines `fortex_auth_token`, not `fortex_api_token`. This will cause AttributeError at runtime.

---

## CRITICAL ISSUE #2: Missing Dependency

**File:** `backend/requirements.txt`
**Issue:** Missing `email-validator` package

**Current:** (missing)

**Add to requirements.txt:**
```
email-validator>=2.0.0
```

**Why:** Pydantic's `EmailStr` validator requires this package. The app will fail to start without it.

---

## CRITICAL ISSUE #3: No .env.example File

**File:** Create `backend/.env.example`

**Create this file with:**
```bash
# Application
DEBUG=false
LOG_LEVEL=INFO

# Fortex API
FORTEX_API_URL=https://api.fortex-zero.us
FORTEX_AUTH_TOKEN=your_token_here
FORTEX_SYSTEM_NAME=zero

# Fortex UI (Playwright)
FORTEX_UI_URL=https://fortex-zero.us/
FORTEX_UI_USERNAME=your_username
FORTEX_UI_PASSWORD=your_password

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/zeroeld_ai

# Security
SECRET_KEY=generate_with_python_generate_secret_key.py

# Agent Configuration
AGENT_POLLING_INTERVAL_SECONDS=300
AGENT_MAX_CONCURRENT_FIXES=1
AGENT_REQUIRE_APPROVAL=true
AGENT_DRY_RUN_MODE=true

# Playwright
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_SCREENSHOTS_DIR=./screenshots
PLAYWRIGHT_SESSION_DIR=./playwright_data

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Server
HOST=0.0.0.0
PORT=8000
```

**Why:** Developers need a template to understand what environment variables are required.

---

## HIGH PRIORITY: Remove Hardcoded Token

**File:** `backend/app/config.py`
**Line:** 24

**Current Code:**
```python
fortex_auth_token: str = "y3He9C57ecfmMAsR19"
```

**Fixed Code:**
```python
fortex_auth_token: str  # No default - must be provided via env var
```

**Why:** Security risk to have tokens in source code, even as defaults.

---

## Verification Steps

After applying fixes, run:

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Check for import errors
python -c "import app.main"

# 3. Run syntax check
python -m py_compile app/main.py test_demo_agent.py

# 4. Start server (should work without errors)
uvicorn app.main:app --reload
```

---

## Timeline
- **Total Fix Time:** 10-15 minutes
- **Testing Time:** 5-10 minutes
- **All fixes can be applied in one commit**

---

## Checklist
- [ ] Fix `fortex_api_token` → `fortex_auth_token` (line 146)
- [ ] Fix `fortex_api_token` → `fortex_auth_token` (line 884)
- [ ] Add `email-validator>=2.0.0` to requirements.txt
- [ ] Create `.env.example` with all variables
- [ ] Remove default value from `fortex_auth_token` in config.py
- [ ] Run verification steps above
- [ ] Commit fixes

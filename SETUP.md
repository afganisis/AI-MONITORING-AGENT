# AI Agent Setup Guide

## Обзор системы

AI Agent автоматически обнаруживает и исправляет ELD нарушения LOW severity через:
- **Fortex API** - чтение violations
- **Playwright** - UI automation для исправления
- **WebSocket** - real-time updates в dashboard
- **PostgreSQL** - хранение errors и fixes

---

## Требования

### Backend
- Python 3.10+
- PostgreSQL 14+ (или Supabase)
- Node.js 18+ (для Playwright)

### Frontend
- Node.js 18+
- npm или yarn

---

## Установка Backend

### 1. Установить зависимости

```bash
cd backend
pip install -r requirements.txt
```

### 2. Установить Playwright browsers

```bash
playwright install chromium
```

### 3. Настроить .env

Скопировать `.env.example` в `.env` и заполнить:

```bash
cp ../.env.example .env
```

**Обязательные переменные:**
```env
# Fortex API
FORTEX_API_URL=https://api.fortex-zero.us
FORTEX_AUTH_TOKEN=y3He9C57ecfmMAsR19
FORTEX_SYSTEM_NAME=zero

# Fortex UI (для Playwright)
FORTEX_UI_URL=https://fortex-zero.us/
FORTEX_UI_USERNAME=ваш_username
FORTEX_UI_PASSWORD=ваш_password

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aiagent

# Security
SECRET_KEY=случайная-строка-минимум-32-символа
```

### 4. Создать базу данных

```bash
# PostgreSQL
createdb aiagent

# Или через psql
psql -U postgres -c "CREATE DATABASE aiagent;"
```

### 5. Запустить сервер

```bash
cd backend
python -m app.main
# или
uvicorn app.main:app --reload
```

API доступен на `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## Установка Frontend

### 1. Установить зависимости

```bash
cd frontend
npm install
```

### 2. Запустить dev server

```bash
npm run dev
```

Frontend доступен на `http://localhost:5173`

---

## Использование AI Agent

### 1. Запуск через API

```bash
# Запустить agent
curl -X POST http://localhost:8000/api/agent/start

# Проверить статус
curl http://localhost:8000/api/agent/status

# Остановить agent
curl -X POST http://localhost:8000/api/agent/stop
```

### 2. Запуск через Dashboard

1. Открыть `http://localhost:5173`
2. Перейти в "Agent Control"
3. Нажать "Start Agent"
4. Наблюдать real-time updates в dashboard

### 3. Настройка компаний для мониторинга

```python
# В Python коде или через API endpoint
from app.agent.background_service import agent_service

# Установить конкретные company IDs
agent_service.set_company_ids([
    "company-uuid-1",
    "company-uuid-2",
    "company-uuid-3"
])
```

**Или через API (нужно добавить endpoint):**
```bash
curl -X POST http://localhost:8000/api/agent/companies \
  -H "Content-Type: application/json" \
  -d '{"company_ids": ["uuid1", "uuid2"]}'
```

---

## Архитектура

```
┌─────────────────┐
│  Fortex API     │ ← Polling каждые 5 мин
└────────┬────────┘
         ↓
┌────────────────────────┐
│ Agent Background       │
│ Service                │
│ - Poll errors          │
│ - Classify (LOW only)  │
│ - Execute fixes        │
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ Playwright Browser     │
│ - Login to Fortex UI   │
│ - Navigate to errors   │
│ - Click/Fill/Submit    │
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ Database + WebSocket   │
│ - Store errors/fixes   │
│ - Broadcast events     │
└────────┬───────────────┘
         ↓
┌────────────────────────┐
│ Frontend Dashboard     │
│ - Real-time updates    │
│ - Agent control        │
└────────────────────────┘
```

---

## LOW Severity Errors (v1)

Agent автоматически исправляет 7 типов ошибок:

1. **diagnosticEvent** - Диагностические события
2. **noShutdownError** - Отсутствие shutdown
3. **noPowerUpError** - Отсутствие power-up
4. **excessiveLogInWarning** - Чрезмерные login
5. **excessiveLogOutWarning** - Чрезмерные logout
6. **eventHasManualLocation** - Ручной ввод локации
7. **eventIsNotDownloaded** - События не загружены

---

## Конфигурация Agent

### Через .env (defaults):
```env
AGENT_POLLING_INTERVAL_SECONDS=300  # 5 минут
AGENT_MAX_CONCURRENT_FIXES=1        # Одновременно
AGENT_REQUIRE_APPROVAL=false        # Автоматически
AGENT_DRY_RUN_MODE=false            # Реальные изменения
```

### Через API (runtime):
```bash
curl -X PATCH http://localhost:8000/api/agent/config \
  -H "Content-Type: application/json" \
  -d '{
    "polling_interval_seconds": 600,
    "max_concurrent_fixes": 2,
    "require_approval": true,
    "dry_run_mode": false
  }'
```

---

## Troubleshooting

### Playwright не запускается

```bash
# Переустановить browsers
playwright install --force chromium

# Проверить headless mode
# В .env установить:
PLAYWRIGHT_HEADLESS=false
```

### Ошибки базы данных

```bash
# Проверить подключение
psql $DATABASE_URL

# Пересоздать таблицы (ОСТОРОЖНО: удалит данные)
# В Python:
from app.database.session import engine, Base
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)
    await conn.run_sync(Base.metadata.create_all)
```

### Agent не находит ошибки

1. Проверить Fortex API credentials:
```bash
curl -H "Authorization: y3He9C57ecfmMAsR19" \
     -H "x-system-name: zero" \
     https://api.fortex-zero.us/monitoring
```

2. Проверить company IDs настроены
3. Проверить логи: `tail -f backend/logs/agent.log`

### WebSocket не подключается

1. Проверить CORS settings в `.env`
2. Проверить WebSocket endpoint доступен: `ws://localhost:8000/ws`
3. Проверить frontend URL в `CORS_ORIGINS`

---

## Логи

### Backend logs
```bash
# Loguru выводит в stdout
# Для сохранения в файл добавить в main.py:
logger.add("logs/agent.log", rotation="1 day", retention="7 days")
```

### Playwright screenshots
Сохраняются в `./screenshots/` при ошибках

### Database audit log
Все действия логируются в таблицу `audit_log`

---

## Production Deployment

### Рекомендации:

1. **Headless mode**: `PLAYWRIGHT_HEADLESS=true`
2. **Debug off**: `DEBUG=false`
3. **Secure secret**: Сгенерировать длинный SECRET_KEY
4. **Database backups**: Настроить автоматические бэкапы
5. **Monitoring**: Добавить Sentry/DataDog
6. **SSL**: Использовать HTTPS для API и WebSocket

### Systemd service (Linux):

```ini
# /etc/systemd/system/aiagent.service
[Unit]
Description=AI Agent Backend
After=network.target postgresql.service

[Service]
Type=simple
User=aiagent
WorkingDirectory=/opt/aiagent/backend
Environment="PATH=/opt/aiagent/venv/bin"
ExecStart=/opt/aiagent/venv/bin/python -m app.main
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Следующие шаги

### v2 Features:
- MEDIUM severity fixes (8 типов)
- HIGH severity fixes (6 типов)
- Manual approval workflow UI
- Email notifications
- Multi-company dashboard
- Advanced analytics

### Frontend TODO:
- Интегрировать с backend API (заменить mock data)
- Добавить WebSocket connection
- Реализовать Agent Control
- Добавить Error List filtering
- Approval workflow UI

---

## Поддержка

- GitHub Issues: https://github.com/your-repo/issues
- Документация API: http://localhost:8000/docs
- План реализации: `C:\Users\AFGANISIS\.claude\plans\swift-dreaming-charm.md`

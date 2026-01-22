# AI Monitoring Agent для ZeroELD

Интеллектуальная система автоматического мониторинга и исправления ошибок ELD (Electronic Logging Device) compliance в системе ZeroELD Cloud.

## 🎯 Возможности

- **Автоматический мониторинг** - постоянное сканирование логов водителей на наличие ошибок
- **AI-агент для исправлений** - автоматическое или с подтверждением исправление 23 типов ошибок
- **Real-time уведомления** - WebSocket обновления о найденных ошибках и исправлениях
- **Dashboard** - визуализация статистики, графики, аналитика
- **Аудит лог** - полная история всех действий агента
- **Гибкая настройка** - настройка правил для каждого типа ошибок

## 🏗️ Архитектура

```
AI MONITORING/
├── backend/              # FastAPI + Python
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── database/     # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   └── zeroeld/      # ZeroELD API client
│   └── requirements.txt
│
└── frontend/             # React + TypeScript
    ├── src/
    │   ├── components/   # UI components
    │   ├── pages/        # Page components
    │   └── utils/        # Utilities
    └── package.json
```

## 🚀 Быстрый старт

### Требования

- Python 3.11+
- Node.js 18+
- PostgreSQL (или Supabase account)
- ZeroELD API credentials

### 1. Backend Setup

```bash
cd backend

# Создать виртуальное окружение (если еще не создано)
python -m venv venv

# Активировать
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Настроить .env файл (см. backend/SETUP.md)
# Заполнить ZEROELD_USERNAME, ZEROELD_PASSWORD, DATABASE_URL, SECRET_KEY

# Сгенерировать SECRET_KEY
python generate_secret_key.py

# Запустить сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен на http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev server
npm run dev
```

Frontend будет доступен на http://localhost:5173

## 📖 Документация

- **Backend Setup**: [backend/SETUP.md](backend/SETUP.md) - подробная инструкция по настройке backend
- **API Documentation**: http://localhost:8000/docs - после запуска backend
- **ZeroELD API**: [backend/ZEROELD_API_DOCUMENTATION.md](backend/ZEROELD_API_DOCUMENTATION.md)
- **Claude Guide**: [backend/CLAUDE.md](backend/CLAUDE.md) - руководство для разработки

## 🔍 Типы ошибок

Система обрабатывает 23 типа ELD compliance ошибок:

### Критические (Critical)
- Sequential ID Break Warning
- No Data in Odometer or Engine Hours Error

### Высокий приоритет (High)
- Odometer Error
- Engine Hours After Shutdown Warning
- Location Changed Error
- Location Error
- Incorrect Status Placement Error
- Speed Much Higher Than Speed Limit

### Средний приоритет (Medium)
- Incorrect Intermediate Placement Error
- Two Identical Statuses Error
- Location Did Not Change Warning
- Driving Origin Warning
- Missing Intermediate Error
- Speed Higher Than Speed Limit
- Unidentified Driver Event

### Низкий приоритет (Low)
- Diagnostic Event
- No Shutdown Error
- No Power Up Error
- Excessive Log In/Out Warning
- Event Has Manual Location
- Event Is Not Downloaded

## 🎨 UI Компоненты

- **Dashboard** - главная страница с общей статистикой и графиками
- **Error List** - список всех ошибок с фильтрами и поиском
- **Agent Control** - управление AI агентом (start/stop/pause/config)
- **Fixes** - история исправлений
- **Audit Log** - журнал всех действий
- **Settings** - настройки системы

## 🛠️ Технологии

### Backend
- FastAPI - современный async веб-фреймворк
- SQLAlchemy 2.0 - ORM для работы с БД
- PostgreSQL - основная БД
- httpx/aiohttp - асинхронные HTTP клиенты
- Pydantic - валидация данных
- Loguru - логирование

### Frontend
- React 18 - UI библиотека
- TypeScript - типизация
- Vite - сборщик
- Tailwind CSS - стилизация
- Recharts - графики
- Zustand - state management
- React Router - роутинг

## 📊 API Endpoints

### Health
- `GET /health` - проверка здоровья сервиса

### Agent Control
- `GET /api/agent/status` - статус агента
- `POST /api/agent/start` - запустить агента
- `POST /api/agent/stop` - остановить агента
- `POST /api/agent/pause` - поставить на паузу
- `PATCH /api/agent/config` - обновить конфигурацию
- `GET /api/agent/stats` - статистика работы

### Errors
- `GET /api/errors` - список ошибок
- `GET /api/errors/{id}` - детали ошибки
- `POST /api/errors/scan` - запустить сканирование
- `DELETE /api/errors/{id}` - удалить ошибку

### Fixes
- `GET /api/fixes` - список исправлений
- `GET /api/fixes/{id}` - детали исправления
- `POST /api/fixes/{id}/approve` - одобрить исправление
- `POST /api/fixes/{id}/reject` - отклонить исправление

## 🔐 Безопасность

- JWT токены для аутентификации в ZeroELD API
- SECRET_KEY для внутренней безопасности
- CORS настройки
- Audit log всех действий
- Dry-run режим для тестирования
- Требование подтверждения для критических операций

## 📝 Конфигурация агента

```env
AGENT_POLLING_INTERVAL_SECONDS=300  # Частота проверки (5 мин)
AGENT_MAX_CONCURRENT_FIXES=1        # Одновременных исправлений
AGENT_REQUIRE_APPROVAL=True         # Требовать подтверждение
AGENT_DRY_RUN_MODE=True            # Режим без изменений (тест)
```

## 🧪 Разработка

### Backend тесты
```bash
cd backend
pytest
```

### Frontend тесты
```bash
cd frontend
npm test
```

### Линтинг
```bash
# Backend
cd backend
flake8 app/
black app/ --check
mypy app/

# Frontend
cd frontend
npm run lint
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is private and proprietary.

## 👥 Authors

- Development Team

## 🐛 Issues

Если нашли баг или у вас есть предложения, создайте issue в репозитории.

## 📞 Support

Для поддержки обратитесь к команде разработки.

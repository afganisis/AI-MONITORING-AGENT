# ZeroELD AI Agent - Frontend

Админ-панель для управления AI Agent системой автоматического исправления ошибок ZeroELD.

## Технологии

- **React 18** - UI фреймворк
- **TypeScript** - Типизация
- **Vite** - Сборщик и dev server
- **Tailwind CSS** - Стилизация
- **React Router** - Навигация
- **Lucide React** - Иконки

## Установка

```bash
# Установить зависимости
npm install

# Запустить dev server
npm run dev

# Собрать для production
npm run build

# Preview production build
npm run preview
```

## Структура проекта

```
src/
├── components/       # Переиспользуемые компоненты
│   ├── common/       # Базовые UI компоненты (Button, Card, Badge)
│   └── layout/       # Layout компоненты (Sidebar, Header)
├── pages/            # Страницы приложения
│   ├── Dashboard/    # Главная страница с статистикой
│   ├── Errors/       # Список ошибок с фильтрами
│   └── Agent/        # Управление AI Agent
├── types/            # TypeScript типы
├── utils/            # Утилиты (форматирование, helpers)
├── data/             # Mock данные для тестирования
└── App.tsx           # Главный компонент с роутингом
```

## Основные страницы

### Dashboard (/)
- Карточки со статистикой (всего ошибок, исправлено сегодня, pending, success rate)
- Графики распределения ошибок по severity и status
- Таблица последних обнаруженных ошибок
- Статус AI Agent

### Errors (/errors)
- Полный список всех ошибок
- Фильтрация по severity, status, error type
- Поиск по driver, error message
- Экспорт данных

### Agent Control (/agent)
- Управление состоянием Agent (start/stop/pause)
- Настройка safety settings (dry run mode, manual approval)
- Operational settings (polling interval, max concurrent fixes)
- Activity log последних действий

## Mock данные

Текущая версия использует mock данные из `src/data/mockData.ts` для тестирования UI. После создания backend API, нужно будет:

1. Создать API клиент в `src/services/api.ts`
2. Добавить WebSocket подключение для real-time updates
3. Заменить mock данные на реальные API вызовы

## Следующие шаги

- [ ] Добавить страницу Fixes с pending approvals
- [ ] Добавить Audit Log страницу
- [ ] Добавить Settings страницу
- [ ] Интегрировать с backend API
- [ ] Добавить WebSocket для live updates
- [ ] Добавить Error Detail модальное окно
- [ ] Добавить тесты (Vitest + React Testing Library)

## Dev Server

После запуска `npm run dev`, приложение будет доступно по адресу:
- http://localhost:3000

API прокси настроен на:
- http://localhost:8000 (FastAPI backend)

## Дизайн

Приложение использует современный дизайн с:
- Светлая тема (можно добавить dark mode позже)
- Цветовая схема:
  - Primary (синий) - основные действия
  - Success (зеленый) - успешные операции
  - Danger (красный) - ошибки и критические действия
  - Warning (оранжевый) - предупреждения
- Адаптивная верстка (desktop first, но responsive)

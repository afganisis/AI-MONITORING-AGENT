"""Служба сканирования логов через Playwright (из test_demo_agent.py)."""

import asyncio
import json
import platform
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger

# Fix Playwright subprocess issue on Windows with Python 3.13+
# Must be set BEFORE importing playwright-related modules
if platform.system() == 'Windows':
    try:
        # Check if event loop policy is already set correctly
        policy = asyncio.get_event_loop_policy()
        if not isinstance(policy, asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            logger.info("Set WindowsProactorEventLoopPolicy for Playwright compatibility")
    except Exception as e:
        logger.warning(f"Could not set event loop policy: {e}")

from app.playwright.browser_manager import BrowserManager
from app.config import get_settings
from app.services.progress_tracker import progress_tracker
from app.database.session import get_db_session
from app.database.models import Error

settings = get_settings()


class LogScannerService:
    """Служба для сканирования логов драйверов через Fortex UI."""

    # Максимум 2 вкладки одновременно чтобы избежать race condition
    MAX_CONCURRENT_TABS = 2

    def __init__(self):
        """Инициализация службы сканирования логов."""
        self.browser_manager: BrowserManager | None = None
        self.logs_dir = Path(settings.playwright_screenshots_dir).parent / "logs_data"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        # Semaphore для ограничения параллельных вкладок
        self._tab_semaphore: asyncio.Semaphore | None = None

    async def scan_driver_logs(
        self,
        driver_id: str,
        driver_name: str = None,
        company_name: str = None,
        company_id: str = None,
        scan_id: str = None,
        days_back: int = 9
    ) -> Dict[str, Any]:
        """
        Сканирует логи одного драйвера через Fortex UI.

        Args:
            driver_id: ID драйвера
            driver_name: Имя драйвера (опционально)
            company_name: Имя компании (опционально)
            company_id: ID компании (опционально)
            scan_id: ID скана для отслеживания прогресса
            days_back: Количество дней назад для сканирования (по умолчанию 9)

        Returns:
            Результаты сканирования с логами и обнаруженными проблемами
        """
        logger.info(f"🔍 Начинаем сканирование логов для драйвера {driver_id[:8]}...")

        # Вычисляем даты
        today = datetime.now()
        start_date = today - timedelta(days=days_back - 1)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = today.strftime("%Y-%m-%d")

        try:
            # Инициализируем браузер
            if not self.browser_manager:
                if scan_id:
                    progress_tracker.update_step(scan_id, 'browser_init', 'Инициализация браузера...')

                self.browser_manager = BrowserManager(
                    headless=settings.playwright_headless,
                    user_data_dir=settings.playwright_session_dir,
                    screenshot_dir=settings.playwright_screenshots_dir,
                )
                await self.browser_manager.initialize()
                logger.info("✅ Браузер инициализирован")

                # Логин в Fortex
                if scan_id:
                    progress_tracker.update_step(scan_id, 'login', 'Вход в систему Fortex...')
                await self._login()

            page = self.browser_manager.page

            # Переход на страницу Activity
            if scan_id:
                progress_tracker.update_step(scan_id, 'navigate', 'Переход на страницу Activity...')
            logger.info("📍 Переход на страницу Activity...")
            await page.goto(f"{settings.fortex_ui_url.rstrip('/')}/activity", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(5000)  # Увеличили таймаут для полной загрузки

            # Сделаем скриншот перед выбором компании
            await self.browser_manager.capture_screenshot("before_company_select")

            # Блокируем form submit (safety net)
            try:
                await page.evaluate('''
                    () => {
                        document.querySelectorAll('form').forEach(form => {
                            form.addEventListener('submit', (e) => { e.preventDefault(); return false; }, true);
                        });
                    }
                ''')
            except Exception as e:
                logger.warning(f"⚠️ Не удалось заблокировать form submit: {e}")

            if scan_id:
                progress_tracker.update_message(scan_id, f"Выбор компании и драйвера...")
                progress_tracker.update_step(scan_id, 'select_company', 'Выбор компании...')

            # Выбор компании (если указана)
            if company_name:
                await self._select_company(page, company_name)
            else:
                # Выбираем первую компанию
                await self._select_first_company(page)

            # Выбор драйвера
            if scan_id:
                progress_tracker.update_step(scan_id, 'select_driver', f'Выбор драйвера {driver_name or driver_id[:8]}...')
            await self._select_driver_by_id(page, driver_id, driver_name)

            # Нажимаем CREATE (открывается новая вкладка)
            if scan_id:
                progress_tracker.update_message(scan_id, f"Открытие логов драйвера...")
                progress_tracker.update_step(scan_id, 'create', 'Открытие новой вкладки логов...')

            page = await self._click_create(page)

            # Устанавливаем даты
            if scan_id:
                progress_tracker.update_message(scan_id, f"Установка диапазона дат ({start_date_str} - {end_date_str})...")
                progress_tracker.update_step(scan_id, 'set_dates', f'Установка дат: {start_date_str} - {end_date_str}...')

            await self._set_date_range(page, start_date, today)

            # Нажимаем LOAD
            if scan_id:
                progress_tracker.update_message(scan_id, f"Загрузка логов...")
                progress_tracker.update_step(scan_id, 'load', 'Нажатие LOAD, загрузка логов...')

            await self._click_load(page)

            # Извлекаем логи
            if scan_id:
                progress_tracker.update_message(scan_id, f"Извлечение логов из таблицы...")
                progress_tracker.update_step(scan_id, 'extract', 'Извлечение логов из таблицы...')

            logs_data = await self._extract_logs(page)

            logger.info(f"✅ Извлечено {len(logs_data)} записей логов")

            # Анализируем логи на проблемы
            if scan_id:
                progress_tracker.update_message(scan_id, f"Анализ логов на ошибки...")
                progress_tracker.update_step(scan_id, 'analyze', f'Анализ {len(logs_data)} записей логов...')

            issues = self._analyze_logs(logs_data)

            # Сохраняем результаты
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            driver_short = driver_id[:8]

            logs_file = self.logs_dir / f"logs_{driver_short}_{timestamp}.json"
            self._save_logs(logs_file, logs_data, driver_id, driver_name, start_date_str, end_date_str)

            if scan_id:
                progress_tracker.update_step(scan_id, 'save_files', 'Сохранение файлов логов...')

            if issues:
                issues_file = self.logs_dir / f"issues_{driver_short}_{timestamp}.json"
                self._save_issues(issues_file, issues)

                # Сохраняем проблемы в базу данных
                if scan_id:
                    progress_tracker.update_message(scan_id, f"Сохранение {len(issues)} проблем в БД...")
                    progress_tracker.update_step(scan_id, 'save_db', f'Сохранение {len(issues)} ошибок в БД...')

                await self._save_issues_to_db(
                    issues=issues,
                    driver_id=driver_id,
                    driver_name=driver_name or f"driver_{driver_short}",
                    company_id=company_id or "unknown",
                    company_name=company_name
                )

            logger.info(f"✅ Сканирование логов завершено: {len(logs_data)} записей, {len(issues)} проблем")

            return {
                'success': True,
                'driver_id': driver_id,
                'driver_name': driver_name or f"driver_{driver_short}",
                'company_name': company_name,
                'total_logs': len(logs_data),
                'issues_found': len(issues),
                'logs_file': str(logs_file),
                'issues_file': str(issues_file) if issues else None,
                'date_range': {
                    'start': start_date_str,
                    'end': end_date_str
                }
            }

        except Exception as e:
            logger.exception(f"❌ Ошибка сканирования логов для драйвера {driver_id[:8]}: {e}")
            return {
                'success': False,
                'driver_id': driver_id,
                'error': str(e)
            }

    async def scan_drivers_parallel(
        self,
        drivers: List[Dict[str, str]],
        company_name: str = None,
        company_id: str = None,
        scan_id: str = None,
        days_back: int = 9
    ) -> List[Dict[str, Any]]:
        """
        Сканирует нескольких драйверов с ограниченной параллельностью.

        ВАЖНО: Используем Semaphore для ограничения до MAX_CONCURRENT_TABS вкладок,
        чтобы избежать race condition при выборе элементов на странице.

        Args:
            drivers: Список драйверов с ключами 'driver_id' и 'driver_name'
            company_name: Название компании
            company_id: ID компании
            scan_id: ID сканирования для прогресса
            days_back: Сколько дней назад сканировать

        Returns:
            Список результатов для каждого драйвера
        """
        logger.info(f"🚀 Сканирование {len(drivers)} драйверов (макс. {self.MAX_CONCURRENT_TABS} параллельно)...")

        # Инициализируем Semaphore для ограничения параллельности
        self._tab_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_TABS)

        # Вычисляем даты один раз для всех
        today = datetime.now()
        start_date = today - timedelta(days=days_back - 1)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = today.strftime("%Y-%m-%d")

        try:
            # Инициализируем браузер один раз
            if not self.browser_manager:
                if scan_id:
                    progress_tracker.update_step(scan_id, 'browser_init', 'Инициализация браузера...')

                self.browser_manager = BrowserManager(
                    headless=settings.playwright_headless,
                    user_data_dir=settings.playwright_session_dir,
                    screenshot_dir=settings.playwright_screenshots_dir,
                )
                await self.browser_manager.initialize()
                logger.info("✅ Браузер инициализирован")

                # Логин в Fortex один раз
                if scan_id:
                    progress_tracker.update_step(scan_id, 'login', 'Вход в систему Fortex...')
                await self._login()

            # Создаем задачи для сканирования С СЕМАФОРОМ
            tasks = []
            for idx, driver_info in enumerate(drivers):
                driver_id = driver_info.get('driver_id')
                driver_name = driver_info.get('driver_name')

                if scan_id:
                    progress_tracker.update_driver(scan_id, idx, driver_id)

                # Оборачиваем в семафор для ограничения параллельности
                task = self._scan_with_semaphore(
                    driver_id=driver_id,
                    driver_name=driver_name,
                    company_name=company_name,
                    company_id=company_id,
                    start_date_str=start_date_str,
                    end_date_str=end_date_str,
                    scan_id=scan_id,
                    driver_index=idx,
                    total_drivers=len(drivers)
                )
                tasks.append(task)

            # Запускаем задачи (Semaphore ограничит параллельность)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Обрабатываем результаты
            final_results = []
            successful_count = 0
            failed_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Драйвер {drivers[i].get('driver_id')[:8]} провалился: {result}")
                    final_results.append({
                        'success': False,
                        'driver_id': drivers[i].get('driver_id'),
                        'error': str(result)
                    })
                    failed_count += 1
                else:
                    final_results.append(result)
                    if result.get('success'):
                        successful_count += 1
                    else:
                        failed_count += 1

            # Определяем общий успех: считаем успешным если хотя бы 1 драйвер просканирован
            overall_success = successful_count > 0

            # NOTE: НЕ вызываем complete_scan здесь!
            # Это делает вызывающий код (agent.py) после дополнительной обработки (сохранение в БД и т.д.)
            # Иначе возникает race condition: frontend может увидеть "completed" раньше,
            # чем agent.py закончит сохранять результаты в БД

            logger.info(f"✅ Сканирование завершено: {successful_count} успешно, {failed_count} провалились")
            return final_results

        except Exception as e:
            logger.exception(f"❌ Ошибка сканирования: {e}")
            # При ошибке ТОЖЕ не вызываем complete_scan - это делает вызывающий код
            raise

    async def _scan_with_semaphore(
        self,
        driver_id: str,
        driver_name: str,
        company_name: str,
        company_id: str,
        start_date_str: str,
        end_date_str: str,
        scan_id: str,
        driver_index: int,
        total_drivers: int
    ) -> Dict[str, Any]:
        """Оборачивает сканирование в Semaphore для ограничения параллельности."""
        async with self._tab_semaphore:
            logger.info(f"[{driver_index + 1}/{total_drivers}] 🔓 Semaphore acquired, начинаю сканирование {driver_name or driver_id[:8]}...")
            result = await self._scan_single_driver_in_new_tab(
                driver_id=driver_id,
                driver_name=driver_name,
                company_name=company_name,
                company_id=company_id,
                start_date_str=start_date_str,
                end_date_str=end_date_str,
                scan_id=scan_id,
                driver_index=driver_index,
                total_drivers=total_drivers
            )
            logger.info(f"[{driver_index + 1}/{total_drivers}] 🔒 Semaphore released")
            return result

    async def _scan_single_driver_in_new_tab(
        self,
        driver_id: str,
        driver_name: str,
        company_name: str,
        company_id: str,
        start_date_str: str,
        end_date_str: str,
        scan_id: str,
        driver_index: int,
        total_drivers: int
    ) -> Dict[str, Any]:
        """Сканирует одного драйвера в отдельной вкладке."""
        try:
            logger.info(f"[{driver_index + 1}/{total_drivers}] 🚀 Начало сканирования:")
            logger.info(f"  - Компания: {company_name or 'не указана'}")
            logger.info(f"  - Драйвер: {driver_name or driver_id[:8]}")
            logger.info(f"  - Driver ID: {driver_id}")
            logger.info(f"  - Company ID: {company_id}")

            # Создаем новую вкладку для этого драйвера
            page = await self.browser_manager.context.new_page()

            try:
                # Переход на Activity с увеличенным таймаутом
                logger.info(f"[{driver_index + 1}/{total_drivers}] Переход на /activity...")
                await page.goto(f"{settings.fortex_ui_url.rstrip('/')}/activity", wait_until="networkidle", timeout=60000)

                # КРИТИЧНО: Ждём полной загрузки страницы и всех компонентов
                logger.info(f"[{driver_index + 1}/{total_drivers}] Ожидание полной загрузки страницы...")
                await page.wait_for_timeout(3000)  # Базовое ожидание

                # Ждём появления критических элементов
                try:
                    await page.wait_for_selector('#select-company', state='visible', timeout=15000)
                    logger.info(f"[{driver_index + 1}/{total_drivers}] ✅ Селектор компании готов")
                except Exception as e:
                    logger.error(f"[{driver_index + 1}/{total_drivers}] ❌ Селектор компании не появился: {e}")
                    await self.browser_manager.capture_screenshot(f"ERROR_no_company_selector_{driver_index}")
                    raise Exception(f"Company selector not found after page load")

                logger.info(f"[{driver_index + 1}/{total_drivers}] Страница загружена: {page.url}")

                # Блокируем form submit (safety net)
                try:
                    await page.evaluate('''
                        () => {
                            document.querySelectorAll('form').forEach(form => {
                                form.addEventListener('submit', (e) => { e.preventDefault(); return false; }, true);
                            });
                        }
                    ''')
                    logger.info(f"[{driver_index + 1}/{total_drivers}] ✅ Form submit заблокирован")
                except Exception as e:
                    logger.warning(f"[{driver_index + 1}/{total_drivers}] ⚠️ Не удалось заблокировать form submit: {e}")

                # Выбор компании - ОБЯЗАТЕЛЬНО указываем конкретную компанию
                if not company_name:
                    logger.error(f"[{driver_index + 1}/{total_drivers}] ❌ КРИТИЧЕСКАЯ ОШИБКА: company_name не указан!")
                    raise Exception("company_name is required - cannot select random company")

                logger.info(f"[{driver_index + 1}/{total_drivers}] Выбираем компанию: {company_name}")
                await self._select_company_improved(page, company_name, driver_index, total_drivers)

                # Выбор драйвера с улучшенной логикой
                # RETRY: Если страница обновилась и компания потерялась - выбираем заново
                max_driver_attempts = 2
                for driver_attempt in range(max_driver_attempts):
                    try:
                        logger.info(f"[{driver_index + 1}/{total_drivers}] Выбираем драйвера: {driver_name or driver_id[:8]}")
                        await self._select_driver_improved(page, driver_id, driver_name, driver_index, total_drivers)
                        break  # Успех!
                    except Exception as e:
                        if "Company selection was lost" in str(e) and driver_attempt < max_driver_attempts - 1:
                            logger.warning(f"[{driver_index + 1}/{total_drivers}] ⚠️ Компания потерялась, перевыбираем...")
                            # Ждём загрузки страницы
                            await page.wait_for_timeout(2000)
                            try:
                                await page.wait_for_load_state('networkidle', timeout=10000)
                            except Exception:
                                pass
                            # Пере-выбираем компанию
                            await self._select_company_improved(page, company_name, driver_index, total_drivers)
                        else:
                            raise

                # Нажимаем CREATE (открывается новая вкладка)
                page = await self._click_create(page)

                # Выбираем даты
                await self._select_dates(page, start_date_str, end_date_str)

                # Нажимаем LOAD
                await self._click_load(page)

                # Извлекаем логи
                logs = await self._extract_logs(page)

                # Получаем ошибки из Smart Analyze API
                formatted_issues = []
                if scan_id and company_id:
                    progress_tracker.update_step(scan_id, 'smart_analyze', f'Получение ошибок из Smart Analyze для {driver_name}...')

                try:
                    logger.info(f"[{driver_index + 1}/{total_drivers}] 🤖 Получение Smart Analyze данных...")
                    from app.fortex.client import FortexAPIClient
                    from app.config import get_settings

                    settings_obj = get_settings()
                    fortex = FortexAPIClient(
                        base_url=settings_obj.fortex_api_url,
                        auth_token=settings_obj.fortex_auth_token
                    )

                    # Получаем Smart Analyze для компании
                    smart_result = await fortex.get_smart_analyze(company_id)
                    await fortex.close()

                    # Ищем нашего драйвера в результате
                    if smart_result and smart_result.drivers:
                        for driver_log in smart_result.drivers:
                            driver_log_id = driver_log.driver_id or driver_log.driverId
                            if driver_log_id == driver_id:
                                # Нашли! Конвертируем logCheckErrors в наш формат
                                if driver_log.logCheckErrors:
                                    for error in driver_log.logCheckErrors:
                                        formatted_issues.append({
                                            'error_type': error.errorType or error.eventCode or 'compliance_error',
                                            'error_name': error.errorMessage or 'Compliance Error',
                                            'description': error.errorMessage or '',
                                            'severity': 'high' if 'VIOLATION' in (error.errorMessage or '') else 'medium',
                                            'category': 'compliance',
                                            'metadata': {
                                                'eventCode': error.eventCode,
                                                'errorTime': error.errorTime,
                                                'errorType': error.errorType,
                                                'id': error.id,
                                                'source': 'smart_analyze_api'
                                            }
                                        })
                                    logger.info(f"[{driver_index + 1}/{total_drivers}] ✅ Smart Analyze нашел {len(formatted_issues)} ошибок")
                                else:
                                    logger.info(f"[{driver_index + 1}/{total_drivers}] ✅ Smart Analyze: ошибок не обнаружено")
                                break
                except Exception as e:
                    logger.error(f"[{driver_index + 1}/{total_drivers}] ❌ Ошибка Smart Analyze: {e}")
                    # Если Smart Analyze провалился, используем базовый анализ логов
                    issues = self._analyze_logs(logs)
                    for issue in issues:
                        formatted_issues.append({
                            'error_type': issue.get('issue_type', 'log_error'),
                            'error_name': issue.get('status') or issue.get('notes') or 'Log Error',
                            'description': f"Status: {issue.get('status', 'N/A')}, Notes: {issue.get('notes', 'N/A')}",
                            'severity': 'medium',
                            'category': 'log_scan',
                            'metadata': {
                                'index': issue.get('index'),
                                'time': issue.get('time'),
                                'event': issue.get('event'),
                                'issue_type': issue.get('issue_type'),
                                'source': 'basic_log_analysis'
                            }
                        })

                # Сохраняем в файлы
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                logs_file = self.logs_dir / f"logs_{driver_id[:8]}_{timestamp}.json"
                with open(logs_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)

                issues_file = None
                if formatted_issues:  # FIX: было 'issues', теперь 'formatted_issues'
                    issues_file = self.logs_dir / f"issues_{driver_id[:8]}_{timestamp}.json"
                    with open(issues_file, 'w', encoding='utf-8') as f:
                        json.dump(formatted_issues, f, indent=2, ensure_ascii=False)

                # Сохраняем в БД
                await self._save_logs_to_database(
                    logs=logs,
                    driver_id=driver_id,
                    driver_name=driver_name,
                    company_id=company_id,
                    company_name=company_name
                )

                logger.info(f"[{driver_index + 1}/{total_drivers}] ✅ {driver_name}: {len(logs)} логов, {len(formatted_issues)} проблем")

                return {
                    'success': True,
                    'driver_id': driver_id,
                    'driver_name': driver_name,
                    'total_logs': len(logs),
                    'issues_found': len(formatted_issues),
                    'issues': formatted_issues,  # Ошибки в формате для сохранения в БД
                    'logs_file': str(logs_file),
                    'issues_file': str(issues_file) if formatted_issues else None,
                    'date_range': {
                        'start': start_date_str,
                        'end': end_date_str
                    }
                }

            finally:
                # Закрываем вкладку этого драйвера
                await page.close()

        except Exception as e:
            logger.exception(f"[{driver_index + 1}/{total_drivers}] ❌ Ошибка для {driver_id[:8]}: {e}")
            return {
                'success': False,
                'driver_id': driver_id,
                'driver_name': driver_name,
                'error': str(e)
            }

    async def _login(self):
        """Логин в Fortex UI."""
        logger.info("🔐 Вход в систему Fortex...")
        page = self.browser_manager.page

        await page.goto(settings.fortex_ui_url)
        await page.wait_for_timeout(2000)

        # Проверяем, нужен ли логин
        if "login" not in page.url.lower():
            logger.info("✅ Уже залогинены")
            return

        # Заполняем форму логина
        username_input = await page.wait_for_selector('#basic_username', timeout=10000)
        await username_input.fill(settings.fortex_ui_username)

        password_input = await page.wait_for_selector('#basic_password', timeout=10000)
        await password_input.fill(settings.fortex_ui_password)

        # Нажимаем LOGIN
        login_button = await page.wait_for_selector('button:has-text("LOGIN")', timeout=10000)
        await login_button.click()

        # Ждем навигации
        await page.wait_for_timeout(5000)

        if "login" not in page.url.lower():
            logger.info("✅ Успешный вход!")
        else:
            raise Exception("Не удалось войти в систему")

    async def _wait_for_selector_with_retry(self, page, selector: str, max_attempts: int = 5, wait_between: int = 2000) -> bool:
        """Ожидает появления селектора с несколькими попытками."""
        for attempt in range(max_attempts):
            try:
                logger.info(f"Попытка {attempt + 1}/{max_attempts} найти селектор: {selector}")
                await page.wait_for_selector(selector, timeout=wait_between)
                logger.info(f"✅ Селектор {selector} найден!")
                return True
            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(f"Селектор {selector} не найден, ждём {wait_between}ms и пробуем снова...")
                    await page.wait_for_timeout(wait_between)
                else:
                    logger.error(f"Селектор {selector} не найден после {max_attempts} попыток")
                    await self.browser_manager.capture_screenshot(f"ERROR_selector_{selector.replace('#', '').replace('.', '_')}_not_found")
                    raise Exception(f"Селектор {selector} не найден после {max_attempts} попыток: {e}")
        return False

    async def _debug_screenshot(self, page, name: str):
        """Делает скриншот для отладки на ПРАВИЛЬНОЙ странице (не main page)."""
        try:
            screenshot_dir = Path(settings.playwright_screenshots_dir)
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%H%M%S")
            filepath = screenshot_dir / f"DEBUG_{name}_{timestamp}.png"
            await page.screenshot(path=str(filepath))
            logger.info(f"📸 Скриншот: {filepath.name}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось сделать скриншот {name}: {e}")

    async def _select_company_improved(self, page, company_name: str, driver_index: int = 0, total_drivers: int = 1):
        """
        Выбор компании в Ant Design Select с дебаг-скриншотами на каждом шаге.
        Используем КЛИК ПО КООРДИНАТАМ вместо Enter (Enter вызывает перезагрузку Fortex).
        """
        prefix = f"[{driver_index + 1}/{total_drivers}]"
        logger.info(f"{prefix} 🏢 === НАЧАЛО ВЫБОРА КОМПАНИИ: '{company_name}' ===")

        # Скриншот начального состояния
        await self._debug_screenshot(page, f"company_1_start_{driver_index}")

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                logger.info(f"{prefix} --- Попытка {attempt + 1}/{max_attempts} ---")

                # ШАГ 1: Ждём появления селектора компании
                logger.info(f"{prefix} Шаг 1: Ищем селектор компании...")
                select_found = False
                for selector in ['#select-company', '[id*="company"]', '.ant-select input']:
                    try:
                        await page.wait_for_selector(selector, state='visible', timeout=5000)
                        logger.info(f"{prefix} ✅ Шаг 1: Селектор найден: '{selector}'")
                        select_found = True
                        break
                    except Exception:
                        continue

                if not select_found:
                    # Дампим HTML для отладки
                    html_dump = await page.evaluate('''
                        () => {
                            const selects = document.querySelectorAll('.ant-select');
                            const inputs = document.querySelectorAll('input');
                            return {
                                ant_selects: selects.length,
                                ant_select_ids: Array.from(selects).map(s => s.querySelector('input')?.id || 'no-id'),
                                all_input_ids: Array.from(inputs).map(i => i.id).filter(id => id),
                                url: window.location.href
                            };
                        }
                    ''')
                    logger.error(f"{prefix} ❌ Шаг 1: Селектор НЕ найден! HTML-дамп: {html_dump}")
                    await self._debug_screenshot(page, f"company_ERROR_no_selector_{driver_index}")
                    raise Exception(f"Селектор компании не найден. Дамп: {html_dump}")

                await page.wait_for_timeout(1000)

                # ШАГ 2: Кликаем по РОДИТЕЛЬСКОМУ контейнеру .ant-select
                # (клик по input с force=True может не открыть dropdown правильно)
                logger.info(f"{prefix} Шаг 2: Кликаем по селектору компании...")
                clicked_selector = await page.evaluate('''
                    () => {
                        const input = document.querySelector('#select-company');
                        if (!input) return null;
                        const antSelect = input.closest('.ant-select');
                        if (antSelect) {
                            const selector_el = antSelect.querySelector('.ant-select-selector');
                            if (selector_el) {
                                selector_el.setAttribute('data-pthora-click', 'company');
                                return '[data-pthora-click="company"]';
                            }
                        }
                        return null;
                    }
                ''')

                if clicked_selector:
                    await page.click(clicked_selector)
                    logger.info(f"{prefix} ✅ Шаг 2: Клик по {clicked_selector}")
                else:
                    await page.click('#select-company')
                    logger.info(f"{prefix} ✅ Шаг 2: Клик по #select-company (fallback)")

                await page.wait_for_timeout(800)
                await self._debug_screenshot(page, f"company_2_after_click_{driver_index}")

                # ШАГ 3: Очищаем и вводим имя компании
                logger.info(f"{prefix} Шаг 3: Вводим '{company_name}'...")
                await page.keyboard.press('Control+A')
                await page.wait_for_timeout(100)
                await page.keyboard.press('Backspace')
                await page.wait_for_timeout(100)
                await page.keyboard.type(company_name, delay=80)
                await page.wait_for_timeout(2500)  # Ждём фильтрации Ant Design
                await self._debug_screenshot(page, f"company_3_after_type_{driver_index}")

                # ШАГ 4: Проверяем что dropdown открылся
                logger.info(f"{prefix} Шаг 4: Проверяем dropdown...")
                dropdown_visible = False
                try:
                    await page.wait_for_selector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)', timeout=5000)
                    dropdown_visible = True
                    logger.info(f"{prefix} ✅ Шаг 4: Dropdown виден")
                except Exception:
                    logger.warning(f"{prefix} ⚠️ Шаг 4: Dropdown НЕ виден!")
                    await self._debug_screenshot(page, f"company_ERROR_no_dropdown_{driver_index}")

                if not dropdown_visible:
                    # Пробуем кликнуть ещё раз
                    logger.info(f"{prefix} Повторный клик по селектору...")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    if clicked_selector:
                        await page.click(clicked_selector)
                    else:
                        await page.click('#select-company')
                    await page.wait_for_timeout(500)
                    await page.keyboard.type(company_name, delay=80)
                    await page.wait_for_timeout(2500)
                    try:
                        await page.wait_for_selector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)', timeout=5000)
                        dropdown_visible = True
                    except Exception:
                        pass

                if not dropdown_visible:
                    logger.error(f"{prefix} ❌ Dropdown не открылся после 2 попыток")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    continue

                # ШАГ 5: Находим все опции в dropdown
                logger.info(f"{prefix} Шаг 5: Ищем опции в dropdown...")
                options_info = await page.evaluate('''
                    () => {
                        const dropdown = document.querySelector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)');
                        if (!dropdown) return { found: false, html: 'NO DROPDOWN' };
                        const options = dropdown.querySelectorAll('.ant-select-item-option');
                        return {
                            found: true,
                            count: options.length,
                            texts: Array.from(options).slice(0, 5).map(o => o.textContent?.trim()),
                            html: dropdown.innerHTML.substring(0, 500)
                        };
                    }
                ''')
                logger.info(f"{prefix} Опции в dropdown: {options_info}")
                await self._debug_screenshot(page, f"company_5_dropdown_options_{driver_index}")

                if not options_info.get('found') or options_info.get('count', 0) == 0:
                    logger.warning(f"{prefix} ⚠️ Нет опций в dropdown!")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    continue

                # ШАГ 6: Находим подходящую опцию и КЛИКАЕМ по координатам
                logger.info(f"{prefix} Шаг 6: Кликаем по опции...")
                first_option = await page.query_selector('.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:first-child')

                if not first_option:
                    # Пробуем альтернативный селектор
                    first_option = await page.query_selector('.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item:first-child')

                clicked = False
                if first_option:
                    option_text = await first_option.text_content()
                    option_text = (option_text or "").strip()
                    logger.info(f"{prefix} Первая опция: '{option_text}'")

                    # Проверяем соответствие
                    norm_search = company_name.strip().lower()
                    norm_result = option_text.lower().replace("  eld", "").replace(" eld", "").strip()
                    if norm_search not in norm_result and norm_result not in norm_search:
                        logger.warning(f"{prefix} ⚠️ Результат '{option_text}' не похож на '{company_name}', но кликаем...")

                    # КЛИК ПО КООРДИНАТАМ (НЕ Enter!)
                    box = await first_option.bounding_box()
                    if box:
                        logger.info(f"{prefix} Bounding box: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")
                        click_x = box['x'] + box['width'] / 2
                        click_y = box['y'] + box['height'] / 2
                        await page.mouse.click(click_x, click_y)
                        logger.info(f"{prefix} ✅ Клик по координатам ({click_x:.0f}, {click_y:.0f})")
                        clicked = True
                    else:
                        logger.warning(f"{prefix} ⚠️ bounding_box вернул None, пробуем force click...")
                        try:
                            await first_option.click(force=True)
                            clicked = True
                            logger.info(f"{prefix} ✅ Force click сработал")
                        except Exception as e:
                            logger.error(f"{prefix} ❌ Force click не сработал: {e}")
                else:
                    logger.error(f"{prefix} ❌ Элемент опции не найден в DOM!")

                if not clicked:
                    logger.error(f"{prefix} ❌ Не удалось кликнуть по опции!")
                    await self._debug_screenshot(page, f"company_ERROR_click_failed_{driver_index}")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    continue

                await page.wait_for_timeout(2000)
                await self._debug_screenshot(page, f"company_6_after_select_{driver_index}")

                # ШАГ 7: ВЕРИФИКАЦИЯ - проверяем что компания выбрана
                logger.info(f"{prefix} Шаг 7: Верификация выбора...")
                selected_value = await page.evaluate('''
                    () => {
                        const input = document.querySelector('#select-company');
                        if (!input) return { value: '', error: 'input not found' };
                        const parent = input.closest('.ant-select');
                        if (!parent) return { value: '', error: 'ant-select parent not found' };
                        const selection = parent.querySelector('.ant-select-selection-item');
                        return {
                            value: selection?.textContent?.trim() || '',
                            hasSelection: !!selection,
                            inputValue: input.value || '',
                            classList: parent.className
                        };
                    }
                ''')
                logger.info(f"{prefix} Результат верификации: {selected_value}")

                selected_text = selected_value.get('value', '') if isinstance(selected_value, dict) else str(selected_value)

                if selected_text and company_name.lower() in selected_text.lower():
                    logger.info(f"{prefix} ✅✅✅ КОМПАНИЯ '{selected_text}' УСПЕШНО ВЫБРАНА!")

                    # Ждём загрузки списка драйверов
                    logger.info(f"{prefix} Ожидание загрузки драйверов...")
                    await page.wait_for_timeout(2000)
                    try:
                        await page.wait_for_load_state('networkidle', timeout=10000)
                    except Exception:
                        pass

                    try:
                        await page.wait_for_selector('#select-driver', state='visible', timeout=15000)
                        logger.info(f"{prefix} ✅ Селектор драйверов готов")
                        await page.wait_for_timeout(1000)
                        await self._debug_screenshot(page, f"company_7_success_{driver_index}")
                        return  # УСПЕХ!
                    except Exception as e:
                        logger.warning(f"{prefix} ⚠️ Селектор драйверов не появился: {e}")
                        await page.wait_for_timeout(3000)
                        await self._debug_screenshot(page, f"company_7_no_driver_select_{driver_index}")
                        return  # Всё равно выходим - компания выбрана

                elif not selected_text:
                    logger.warning(f"{prefix} ⚠️ Компания НЕ выбрана (пусто)! Страница обновилась?")
                    await self._debug_screenshot(page, f"company_ERROR_empty_{driver_index}_{attempt}")
                    await page.wait_for_timeout(1000)
                else:
                    logger.warning(f"{prefix} ⚠️ Выбрано '{selected_text}', ожидали '{company_name}'")
                    await self._debug_screenshot(page, f"company_ERROR_wrong_{driver_index}_{attempt}")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)

            except Exception as e:
                logger.error(f"{prefix} ❌ Ошибка выбора компании (попытка {attempt + 1}): {e}")
                await self._debug_screenshot(page, f"company_ERROR_exception_{driver_index}_{attempt}")
                await page.wait_for_timeout(1000)

        await self._debug_screenshot(page, f"company_FINAL_FAILURE_{driver_index}")
        raise Exception(f"Не удалось выбрать компанию '{company_name}' после {max_attempts} попыток")

    async def _select_driver_improved(self, page, driver_id: str, driver_name: str = None, driver_index: int = 0, total_drivers: int = 1):
        """
        Выбор драйвера в Ant Design Select с дебаг-скриншотами.
        Используем КЛИК ПО КООРДИНАТАМ вместо Enter.
        """
        prefix = f"[{driver_index + 1}/{total_drivers}]"
        search_query = driver_name or driver_id[:8]
        logger.info(f"{prefix} 👤 === НАЧАЛО ВЫБОРА ДРАЙВЕРА: '{search_query}' ===")

        # Ждём стабилизации страницы после выбора компании
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except Exception:
            pass

        # Проверяем что компания всё ещё выбрана
        company_check = await page.evaluate('''
            () => {
                const input = document.querySelector('#select-company');
                const parent = input?.closest('.ant-select');
                const selection = parent?.querySelector('.ant-select-selection-item');
                return selection?.textContent?.trim() || '';
            }
        ''')
        if not company_check:
            logger.error(f"{prefix} ❌ Компания не выбрана! Страница обновилась.")
            await self._debug_screenshot(page, f"driver_ERROR_no_company_{driver_index}")
            raise Exception("Company selection was lost - page may have refreshed")
        logger.info(f"{prefix} ✅ Компания на месте: '{company_check}'")

        await self._debug_screenshot(page, f"driver_1_start_{driver_index}")

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                logger.info(f"{prefix} --- Драйвер: попытка {attempt + 1}/{max_attempts} ---")

                # Ждём селектор драйвера
                await self._wait_for_selector_with_retry(page, '#select-driver', max_attempts=5, wait_between=2000)
                await page.wait_for_timeout(1000)

                # Кликаем по РОДИТЕЛЬСКОМУ .ant-select-selector
                clicked_selector = await page.evaluate('''
                    () => {
                        const input = document.querySelector('#select-driver');
                        if (!input) return null;
                        const antSelect = input.closest('.ant-select');
                        if (antSelect) {
                            const sel = antSelect.querySelector('.ant-select-selector');
                            if (sel) {
                                sel.setAttribute('data-pthora-click', 'driver');
                                return '[data-pthora-click="driver"]';
                            }
                        }
                        return null;
                    }
                ''')

                if clicked_selector:
                    await page.click(clicked_selector)
                else:
                    await page.click('#select-driver')
                await page.wait_for_timeout(800)

                # Очищаем и вводим имя
                await page.keyboard.press('Control+A')
                await page.wait_for_timeout(100)
                await page.keyboard.press('Backspace')
                await page.wait_for_timeout(100)

                logger.info(f"{prefix} Вводим: '{search_query}'")
                await page.keyboard.type(search_query, delay=80)
                await page.wait_for_timeout(2500)
                await self._debug_screenshot(page, f"driver_2_after_type_{driver_index}")

                # Проверяем dropdown
                try:
                    await page.wait_for_selector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)', timeout=5000)
                except Exception:
                    logger.warning(f"{prefix} ⚠️ Dropdown не открылся")
                    await self._debug_screenshot(page, f"driver_ERROR_no_dropdown_{driver_index}")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    continue

                # Ищем опции
                options_info = await page.evaluate('''
                    () => {
                        const dd = document.querySelector('.ant-select-dropdown:not(.ant-select-dropdown-hidden)');
                        if (!dd) return { count: 0 };
                        const opts = dd.querySelectorAll('.ant-select-item-option');
                        return {
                            count: opts.length,
                            texts: Array.from(opts).slice(0, 3).map(o => o.textContent?.trim())
                        };
                    }
                ''')
                logger.info(f"{prefix} Опции: {options_info}")

                if options_info.get('count', 0) == 0:
                    logger.warning(f"{prefix} ⚠️ Нет опций!")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    continue

                # КЛИК ПО КООРДИНАТАМ
                driver_option = await page.query_selector('.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option:first-child')
                clicked = False
                if driver_option:
                    box = await driver_option.bounding_box()
                    if box:
                        await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                        logger.info(f"{prefix} ✅ Клик по драйверу ({box['x']:.0f}, {box['y']:.0f})")
                        clicked = True
                    else:
                        try:
                            await driver_option.click(force=True)
                            clicked = True
                        except Exception:
                            pass

                if not clicked:
                    # Fallback: ArrowDown + click
                    await page.keyboard.press('ArrowDown')
                    await page.wait_for_timeout(300)
                    active = await page.query_selector('.ant-select-item-option-active')
                    if active:
                        box = await active.bounding_box()
                        if box:
                            await page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                            clicked = True

                if not clicked:
                    logger.warning(f"{prefix} ⚠️ Клик не удался")
                    await self._debug_screenshot(page, f"driver_ERROR_click_{driver_index}")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    continue

                await page.wait_for_timeout(2000)

                # Верификация
                selected_value = await page.evaluate('''
                    () => {
                        const input = document.querySelector('#select-driver');
                        const parent = input?.closest('.ant-select');
                        const selection = parent?.querySelector('.ant-select-selection-item');
                        return selection?.textContent?.trim() || '';
                    }
                ''')

                if selected_value:
                    logger.info(f"{prefix} ✅ Драйвер выбран: '{selected_value}'")
                    await self._debug_screenshot(page, f"driver_3_success_{driver_index}")
                    return
                else:
                    logger.warning(f"{prefix} ⚠️ Драйвер не выбран")
                    await self._debug_screenshot(page, f"driver_ERROR_empty_{driver_index}_{attempt}")
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)

            except Exception as e:
                logger.error(f"{prefix} ❌ Ошибка: {e}")
                await self._debug_screenshot(page, f"driver_ERROR_{driver_index}_{attempt}")
                await page.wait_for_timeout(1000)

        raise Exception(f"Не удалось выбрать драйвера '{search_query}' после {max_attempts} попыток")

    async def _select_company(self, page, company_name: str):
        """
        Выбирает компанию используя КЛАВИАТУРНУЮ навигацию Ant Design Select.
        DEPRECATED: Используйте _select_company_improved
        """
        await self._select_company_improved(page, company_name)

    async def _select_first_company(self, page):
        """Выбирает первую доступную компанию."""
        logger.info("🏢 Выбор первой компании...")

        company_input = await page.wait_for_selector('#select-company', timeout=5000)
        parent_selector = await page.evaluate('''
            () => {
                const input = document.querySelector('#select-company');
                const antSelect = input?.closest('.ant-select');
                if (antSelect) {
                    antSelect.setAttribute('data-company-select', 'true');
                    return '[data-company-select="true"]';
                }
                return null;
            }
        ''')

        if parent_selector:
            dropdown = await page.wait_for_selector(parent_selector, timeout=2000)
            await dropdown.click()
            await page.wait_for_timeout(500)

            # Выбираем первую опцию
            first_option = await page.wait_for_selector('.ant-select-item:not(.ant-select-item-option-disabled)', timeout=3000)
            await first_option.click()
            logger.info("✅ Компания выбрана")
            await page.wait_for_timeout(1000)

    async def _select_driver_by_id(self, page, driver_id: str, driver_name: str = None):
        """
        Выбирает драйвера. DEPRECATED: Используйте _select_driver_improved
        """
        await self._select_driver_improved(page, driver_id, driver_name)

    async def _click_create(self, page):
        """Нажимает кнопку CREATE и переключается на новую вкладку."""
        logger.info("🔘 Нажатие кнопки CREATE...")

        create_button = await page.wait_for_selector('button:has-text("CREATE")', timeout=5000)

        async with page.context.expect_page() as new_page_info:
            await create_button.click()

        new_page = await new_page_info.value
        logger.info(f"✅ Новая вкладка открыта: {new_page.url}")

        # Ждем загрузки
        await new_page.wait_for_load_state('networkidle', timeout=15000)
        await new_page.wait_for_timeout(3000)

        return new_page

    async def _select_dates(self, page, start_date_str: str, end_date_str: str):
        """Устанавливает даты из строк (wrapper для _set_date_range)."""
        logger.info(f"📅 Выбор дат: {start_date_str} - {end_date_str}...")

        # Конвертируем строки в datetime
        from datetime import datetime
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        # Вызываем существующий метод
        await self._set_date_range(page, start_date, end_date)

    async def _set_date_range(self, page, start_date: datetime, end_date: datetime):
        """Устанавливает диапазон дат."""
        logger.info(f"📅 Установка дат: {start_date.date()} - {end_date.date()}...")

        # Импортируем helper для установки дат
        try:
            import sys
            from pathlib import Path
            helpers_path = Path(__file__).parent.parent.parent / "helpers"
            if str(helpers_path) not in sys.path:
                sys.path.insert(0, str(helpers_path))

            from date_picker import set_date_range_simple

            date_set = await set_date_range_simple(page, start_date, end_date)

            if date_set:
                logger.info("✅ Даты установлены")
            else:
                logger.warning("⚠️ Не удалось установить даты, используются значения по умолчанию")

            # Закрываем календарь если открыт
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)

        except Exception as e:
            logger.warning(f"⚠️ Ошибка установки дат: {e}")

    async def _click_load(self, page):
        """Нажимает кнопку LOAD и ждёт загрузки данных."""
        logger.info("🔘 Нажатие кнопки LOAD...")

        # Ждём появления кнопки LOAD
        try:
            await page.wait_for_selector('button#load-logs', timeout=15000, state='visible')
            logger.info("✅ Кнопка LOAD найдена")
        except Exception as e:
            logger.warning(f"⚠️ Кнопка load-logs не найдена, пробуем альтернативу: {e}")
            # Пробуем альтернативные селекторы
            try:
                await page.wait_for_selector('button:has-text("LOAD")', timeout=5000)
            except Exception:
                await page.wait_for_selector('button:has-text("Load")', timeout=5000)

        load_button = await page.query_selector('button#load-logs') or await page.query_selector('button:has-text("LOAD")')

        if not load_button:
            logger.error("❌ Кнопка LOAD не найдена!")
            raise Exception("LOAD button not found")

        # Используем координатный клик (самый надёжный для stubborn buttons)
        box = await load_button.bounding_box()
        if box:
            x = box['x'] + box['width'] / 2
            y = box['y'] + box['height'] / 2
            await page.mouse.click(x, y)
            logger.info("✅ Кнопка LOAD нажата (координатный клик)")
        else:
            await load_button.click(force=True)
            logger.info("✅ Кнопка LOAD нажата (force)")

        # КРИТИЧНО: Ждём достаточно времени для загрузки данных
        logger.info("⏳ Ожидание загрузки логов (15 секунд)...")
        await page.wait_for_timeout(15000)

        # Дополнительно ждём пока таблица появится
        try:
            await page.wait_for_selector('.patch-table-row, .ant-table-row, table tbody tr', timeout=10000)
            logger.info("✅ Таблица с логами загружена")
        except Exception:
            logger.warning("⚠️ Таблица может быть пустой или не загружена")

    async def _extract_logs(self, page) -> List[Dict[str, Any]]:
        """Извлекает логи из таблицы."""
        logger.info("📊 Извлечение логов...")

        # Скроллим до конца
        await self._scroll_to_bottom(page)

        # Извлекаем данные
        result = await page.evaluate('''
            () => {
                let rows = document.querySelectorAll('.patch-table-row:not(.patch-table-header)');

                if (rows.length === 0) {
                    rows = document.querySelectorAll('.ant-table-row');
                }

                if (rows.length === 0) {
                    rows = document.querySelectorAll('table tbody tr');
                }

                const logs = [];

                rows.forEach((row, idx) => {
                    let cells = row.querySelectorAll('td');
                    if (cells.length === 0) {
                        cells = Array.from(row.children);
                    }

                    if (cells.length >= 5) {
                        const timeText = cells[0]?.textContent?.trim() || '';
                        const eventText = cells[1]?.textContent?.trim() || '';

                        // Фильтруем строки календаря
                        const isCalendarRow = /^\\d{1,2}$/.test(timeText) && /^\\d{1,2}$/.test(eventText);
                        if (isCalendarRow || (!timeText && !eventText)) {
                            return;
                        }

                        const logEntry = {
                            time: timeText,
                            event: eventText,
                            duration: cells[2]?.textContent?.trim() || '',
                            status: cells[3]?.textContent?.trim() || '',
                            location: cells[4]?.textContent?.trim() || '',
                        };

                        if (cells.length >= 6) logEntry.odometer = cells[5]?.textContent?.trim() || '';
                        if (cells.length >= 7) logEntry.eh = cells[6]?.textContent?.trim() || '';
                        if (cells.length >= 8) logEntry.notes = cells[7]?.textContent?.trim() || '';

                        logs.push(logEntry);
                    }
                });

                return logs;
            }
        ''')

        logger.info(f"✅ Извлечено {len(result)} записей")
        return result

    async def _scroll_to_bottom(self, page):
        """Скроллит таблицу до конца."""
        logger.info("📜 Скроллинг таблицы...")

        prev_rows = 0
        no_change = 0

        for i in range(100):
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await page.wait_for_timeout(200)

            new_rows = await page.evaluate("document.querySelectorAll('table tbody tr, .ant-table-row').length")

            if new_rows != prev_rows:
                no_change = 0
                prev_rows = new_rows
            else:
                no_change += 1
                if no_change >= 5:
                    break

        logger.info(f"✅ Скроллинг завершён")

    def _analyze_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Анализирует логи на проблемы."""
        issues = []

        for idx, log in enumerate(logs):
            # Проверяем status на ошибки
            if log.get('status'):
                status_lower = log['status'].lower()
                if any(keyword in status_lower for keyword in ['error', 'missing', 'violation', 'invalid']):
                    issues.append({
                        'index': idx,
                        'time': log.get('time'),
                        'event': log.get('event'),
                        'status': log.get('status'),
                        'issue_type': 'status_error'
                    })

            # Проверяем notes на ошибки
            if log.get('notes'):
                notes_lower = log['notes'].lower()
                if any(keyword in notes_lower for keyword in ['error', 'fail', 'violation', 'missing']):
                    issues.append({
                        'index': idx,
                        'time': log.get('time'),
                        'event': log.get('event'),
                        'notes': log.get('notes'),
                        'issue_type': 'notes_error'
                    })

        return issues

    def _save_logs(self, file_path: Path, logs: List[Dict], driver_id: str, driver_name: str, start_date: str, end_date: str):
        """Сохраняет логи в JSON файл."""
        data = {
            'meta': {
                'extracted_at': datetime.now().isoformat(),
                'driver_id': driver_id,
                'driver_name': driver_name,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'total_entries': len(logs)
            },
            'data': {
                'logs': logs
            }
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Логи сохранены: {file_path}")

    def _save_issues(self, file_path: Path, issues: List[Dict]):
        """Сохраняет найденные проблемы в JSON файл."""
        data = {
            'status': 'HAS_ERRORS',
            'total_issues': len(issues),
            'issues': issues
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Проблемы сохранены: {file_path}")

    async def _save_logs_to_database(
        self,
        logs: List[Dict[str, Any]],
        driver_id: str,
        driver_name: str,
        company_id: str,
        company_name: str
    ):
        """Анализирует логи и сохраняет найденные проблемы в базу данных."""
        # Анализируем логи на предмет проблем
        issues = self._analyze_logs(logs)

        # Сохраняем найденные проблемы
        if issues:
            logger.info(f"Найдено {len(issues)} проблем для драйвера {driver_name}, сохраняем в БД...")
            await self._save_issues_to_db(
                issues=issues,
                driver_id=driver_id,
                driver_name=driver_name,
                company_id=company_id,
                company_name=company_name
            )
        else:
            logger.info(f"✅ Нет проблем для драйвера {driver_name}")

    async def _save_issues_to_db(
        self,
        issues: List[Dict[str, Any]],
        driver_id: str,
        driver_name: str,
        company_id: str,
        company_name: str
    ):
        """Сохраняет найденные проблемы в базу данных как ошибки."""
        if not issues:
            logger.info("✅ Нет проблем для сохранения в БД")
            return

        try:
            async with get_db_session() as session:
                errors_created = 0

                for idx, issue in enumerate(issues):
                    try:
                        # Определяем тип ошибки
                        error_key = issue.get('issue_type', 'LOG_SCAN_ERROR')

                        # Формируем сообщение об ошибке
                        if issue.get('issue_type') == 'status_error':
                            error_message = f"Status: {issue.get('status', 'Unknown')}"
                            error_name = "Log Status Error"
                            severity = 'high'
                        elif issue.get('issue_type') == 'notes_error':
                            error_message = f"Notes: {issue.get('notes', 'Unknown')}"
                            error_name = "Log Notes Error"
                            severity = 'medium'
                        else:
                            error_message = str(issue)
                            error_name = "Log Scan Error"
                            severity = 'low'

                        # Создаём запись об ошибке
                        db_error = Error(
                            driver_id=driver_id,
                            driver_name=driver_name,
                            company_id=company_id or "unknown",
                            company_name=company_name or "Unknown",
                            error_key=error_key,
                            error_name=error_name,
                            error_message=error_message,
                            severity=severity,
                            status='pending',
                            error_metadata=issue  # Сохраняем полные данные issue
                        )
                        session.add(db_error)
                        errors_created += 1

                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось сохранить проблему {idx + 1}: {e}")

                await session.commit()
                logger.info(f"💾 Успешно сохранено {errors_created}/{len(issues)} ошибок в БД для драйвера {driver_name} ({driver_id[:8]})")

        except Exception as e:
            logger.exception(f"❌ Ошибка при сохранении проблем в БД: {e}")

    async def cleanup(self):
        """Закрывает браузер."""
        if self.browser_manager:
            await self.browser_manager.cleanup()
            self.browser_manager = None
            logger.info("✅ Браузер закрыт")

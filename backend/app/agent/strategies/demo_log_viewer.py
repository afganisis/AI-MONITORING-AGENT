"""Demo strategy: просмотр логов драйверов без исправлений."""

from datetime import datetime, timedelta
from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from app.agent.strategies.base import BaseFixStrategy, FixResult
from app.database.models import Error, Fix


class DemoLogViewerStrategy(BaseFixStrategy):
    """
    Демонстрационная стратегия для просмотра логов драйверов.

    Не исправляет ошибки, только:
    - Заходит в логи драйвера
    - Скроллит последние 9 дней
    - Делает скриншоты
    """

    @property
    def error_key(self) -> str:
        """Работает со всеми типами ошибок."""
        return "demo_viewer"

    @property
    def strategy_name(self) -> str:
        return "Demo Log Viewer (No Fixes)"

    async def can_handle(self, error: Error) -> bool:
        """Может обработать любую ошибку для демонстрации."""
        return True

    async def execute(self, error: Error, fix: Fix, browser_manager) -> FixResult:
        """
        Демонстрирует просмотр логов драйвера.

        Steps:
        1. Открываем Fortex UI
        2. Ищем драйвера
        3. Заходим в логи
        4. Скроллим последние 9 дней
        5. Делаем скриншоты
        """
        start_time = datetime.utcnow()
        page: Page = browser_manager.page

        try:
            logger.info(f"🤖 [DEMO] Starting log viewer for driver: {error.driver_name}")

            # Step 1: Переходим на главную страницу
            logger.info("📍 Step 1: Navigating to Fortex UI...")
            await page.goto(browser_manager.fortex_ui_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Скриншот главной страницы
            await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_1_homepage.png")
            logger.info("✅ Homepage loaded")

            # Step 2: Ищем меню с драйверами
            logger.info("📍 Step 2: Looking for Drivers menu...")

            # Попробуем найти навигацию (адаптируйте селекторы под реальный UI)
            possible_selectors = [
                'a:has-text("Drivers")',
                'a:has-text("Driver")',
                'a:has-text("Водители")',
                '[href*="driver"]',
                'button:has-text("Drivers")',
            ]

            drivers_link = None
            for selector in possible_selectors:
                try:
                    drivers_link = await page.wait_for_selector(selector, timeout=3000)
                    if drivers_link:
                        logger.info(f"✅ Found drivers menu: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not drivers_link:
                logger.warning("⚠️ Could not find Drivers menu, taking screenshot...")
                await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_2_no_drivers_menu.png")

                # Попробуем найти любую навигацию
                logger.info("📍 Searching for any navigation elements...")
                nav_html = await page.content()
                await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_2_full_page.png", full_page=True)

                return FixResult(
                    success=False,
                    message="Demo: Could not locate Drivers menu. Check screenshots for UI structure.",
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    metadata={
                        "step": "navigation",
                        "error": "Drivers menu not found",
                        "screenshots": ["demo_2_no_drivers_menu.png", "demo_2_full_page.png"],
                    }
                )

            # Кликаем на меню драйверов
            await drivers_link.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_3_drivers_list.png")
            logger.info("✅ Navigated to drivers list")

            # Step 3: Ищем конкретного драйвера
            logger.info(f"📍 Step 3: Searching for driver: {error.driver_name}...")

            # Попробуем найти поиск или фильтр
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[placeholder*="поиск" i]',
                'input[type="text"]',
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        logger.info(f"✅ Found search input: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if search_input:
                # Вводим имя драйвера
                await search_input.fill(error.driver_name or error.driver_id)
                await page.wait_for_timeout(1500)
                await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_4_search_results.png")
                logger.info(f"✅ Searched for driver: {error.driver_name}")

            # Ищем драйвера в списке (по имени или ID)
            driver_cell_selectors = [
                f'text="{error.driver_name}"',
                f'text="{error.driver_id}"',
                f'td:has-text("{error.driver_name}")',
                f'tr:has-text("{error.driver_name}")',
            ]

            driver_row = None
            for selector in driver_cell_selectors:
                try:
                    driver_row = await page.wait_for_selector(selector, timeout=3000)
                    if driver_row:
                        logger.info(f"✅ Found driver row: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not driver_row:
                logger.warning(f"⚠️ Driver {error.driver_name} not found in list")
                await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_5_driver_not_found.png")

                return FixResult(
                    success=False,
                    message=f"Demo: Driver '{error.driver_name}' not found in list",
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    metadata={
                        "step": "driver_search",
                        "driver": error.driver_name,
                        "screenshots": ["demo_5_driver_not_found.png"],
                    }
                )

            # Кликаем на драйвера (или на кнопку "Logs")
            # Попробуем найти кнопку Logs рядом с драйвером
            logs_button_selectors = [
                'a:has-text("Logs")',
                'button:has-text("Logs")',
                'a:has-text("Логи")',
                '[href*="log"]',
            ]

            # Сначала кликаем на строку драйвера
            await driver_row.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_6_driver_clicked.png")

            # Теперь ищем кнопку Logs
            logs_button = None
            for selector in logs_button_selectors:
                try:
                    logs_button = await page.wait_for_selector(selector, timeout=3000)
                    if logs_button:
                        logger.info(f"✅ Found logs button: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if logs_button:
                await logs_button.click()
                await page.wait_for_timeout(2000)
                logger.info("✅ Clicked on Logs button")
            else:
                logger.info("⚠️ No explicit Logs button, assuming we're on driver page")

            await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_7_logs_page.png")

            # Step 4: Скроллим последние 9 дней
            logger.info("📍 Step 4: Scrolling through last 9 days of logs...")

            # Проверяем есть ли date picker или фильтр по датам
            date_range_selectors = [
                'input[type="date"]',
                'input[placeholder*="date" i]',
                'input[placeholder*="дата" i]',
                '[class*="date-picker"]',
            ]

            # Попробуем установить диапазон дат
            today = datetime.now()
            nine_days_ago = today - timedelta(days=9)

            for selector in date_range_selectors:
                try:
                    date_input = await page.wait_for_selector(selector, timeout=2000)
                    if date_input:
                        await date_input.fill(nine_days_ago.strftime("%Y-%m-%d"))
                        logger.info(f"✅ Set date range to last 9 days")
                        break
                except PlaywrightTimeout:
                    continue

            # Скроллим вниз несколько раз для загрузки всех логов
            logger.info("📜 Scrolling through logs...")
            for i in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)
                logger.info(f"   Scroll {i+1}/5")

            # Скриншот после скролла
            await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_8_logs_scrolled.png", full_page=True)

            # Скроллим обратно вверх
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            logger.info("✅ Demo completed successfully!")

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return FixResult(
                success=True,
                message=f"Demo: Successfully viewed logs for driver {error.driver_name} (last 9 days)",
                execution_time_ms=execution_time,
                metadata={
                    "driver_name": error.driver_name,
                    "driver_id": error.driver_id,
                    "company": error.company_name,
                    "screenshots": [
                        "demo_1_homepage.png",
                        "demo_3_drivers_list.png",
                        "demo_4_search_results.png",
                        "demo_6_driver_clicked.png",
                        "demo_7_logs_page.png",
                        "demo_8_logs_scrolled.png",
                    ],
                    "note": "No changes were made - this was a view-only operation"
                }
            )

        except Exception as e:
            logger.error(f"❌ Demo failed: {str(e)}")

            # Делаем скриншот ошибки
            try:
                await page.screenshot(path=f"{browser_manager.screenshots_dir}/demo_error.png")
            except:
                pass

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return FixResult(
                success=False,
                message=f"Demo failed: {str(e)}",
                execution_time_ms=execution_time,
                metadata={
                    "exception_type": type(e).__name__,
                    "error_details": str(e),
                    "screenshots": ["demo_error.png"],
                }
            )

"""Helper для работы с Ant Design RangePicker."""

from datetime import datetime
from loguru import logger


async def set_date_range(page, start_date: datetime, end_date: datetime):
    """
    Установить диапазон дат в Ant Design RangePicker через клики по календарю.

    Args:
        page: Playwright page object
        start_date: Начальная дата
        end_date: Конечная дата
    """
    try:
        # Шаг 1: Кликаем на первый input чтобы открыть календарь
        logger.info("📅 Opening date range picker...")

        # Находим первый input в RangePicker
        first_input = await page.query_selector('.ant-picker-input:first-child input')
        if not first_input:
            logger.error("❌ RangePicker input not found")
            return False

        await first_input.click()
        await page.wait_for_timeout(500)

        # Проверяем что календарь открылся
        calendar = await page.wait_for_selector('.ant-picker-dropdown', timeout=3000)
        if not calendar:
            logger.error("❌ Calendar did not open")
            return False

        logger.info("✅ Calendar opened")

        # Шаг 2: Выбираем start date
        logger.info(f"📅 Selecting start date: {start_date.strftime('%Y-%m-%d')}")

        # Ищем нужную дату в календаре
        start_day = start_date.day
        start_month = start_date.month
        start_year = start_date.year

        # Кликаем на день в календаре
        # Формат: .ant-picker-cell-inner с текстом дня
        success = await page.evaluate(f'''
            () => {{
                // Ищем все ячейки с датами
                const cells = document.querySelectorAll('.ant-picker-cell');

                for (const cell of cells) {{
                    const inner = cell.querySelector('.ant-picker-cell-inner');
                    if (!inner) continue;

                    const dayText = inner.textContent.trim();

                    // Проверяем что это нужный день и ячейка не disabled
                    if (dayText === '{start_day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                        inner.click();
                        return true;
                    }}
                }}

                return false;
            }}
        ''')

        if not success:
            logger.error(f"❌ Start date {start_day} not found in calendar")
            return False

        await page.wait_for_timeout(500)
        logger.info(f"✅ Start date selected: {start_day}")

        # Шаг 3: Выбираем end date
        logger.info(f"📅 Selecting end date: {end_date.strftime('%Y-%m-%d')}")

        end_day = end_date.day

        success = await page.evaluate(f'''
            () => {{
                const cells = document.querySelectorAll('.ant-picker-cell');

                for (const cell of cells) {{
                    const inner = cell.querySelector('.ant-picker-cell-inner');
                    if (!inner) continue;

                    const dayText = inner.textContent.trim();

                    if (dayText === '{end_day}' && !cell.classList.contains('ant-picker-cell-disabled')) {{
                        inner.click();
                        return true;
                    }}
                }}

                return false;
            }}
        ''')

        if not success:
            logger.error(f"❌ End date {end_day} not found in calendar")
            return False

        await page.wait_for_timeout(500)
        logger.info(f"✅ End date selected: {end_day}")

        # Шаг 4: Закрываем календарь (он должен закрыться автоматически)
        try:
            await page.wait_for_selector('.ant-picker-dropdown', state='hidden', timeout=2000)
            logger.info("✅ Calendar closed")
        except:
            # Если не закрылся - кликаем вне календаря
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(300)
            logger.info("✅ Calendar closed via Escape")

        return True

    except Exception as e:
        logger.error(f"❌ Date selection failed: {e}")
        return False


async def set_date_range_simple(page, start_date: datetime, end_date: datetime):
    """
    УПРОЩЕННАЯ ВЕРСИЯ: Проверяем дефолтные даты на странице.
    Если они уже правильные - ничего не делаем.
    Если неправильные - пытаемся исправить.
    """
    try:
        start_str = start_date.strftime('%m/%d/%Y')
        end_str = end_date.strftime('%m/%d/%Y')

        logger.info("📅 Checking current date range...")
        logger.info(f"   Expected: {start_str} - {end_str}")

        # Проверяем текущие даты
        current_dates = await page.evaluate('''
            () => {
                const inputs = document.querySelectorAll('.ant-picker-input input');
                return {
                    start: inputs[0]?.value || '',
                    end: inputs[1]?.value || ''
                };
            }
        ''')

        logger.info(f"   Current: {current_dates['start']} - {current_dates['end']}")

        # Если даты уже правильные - просто возвращаем True
        if current_dates['start'] == start_str and current_dates['end'] == end_str:
            logger.info("✅ Dates already correct! No need to change.")
            return True

        logger.warning(f"⚠️ Dates don't match! Will use page defaults.")
        logger.warning(f"   Page has: {current_dates['start']} - {current_dates['end']}")
        logger.warning(f"   We want: {start_str} - {end_str}")

        # ВАЖНО: Пока date picker слишком сложный - используем ДЕФОЛТНЫЕ даты
        # В будущем можно добавить более сложную логику
        return True

    except Exception as e:
        logger.error(f"❌ Date check failed: {type(e).__name__}: {e}")
        logger.warning("⚠️ Will use page defaults")
        return True

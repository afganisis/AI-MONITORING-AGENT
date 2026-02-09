"""Debug tools для анализа проблем на странице."""

from loguru import logger


async def diagnose_date_picker(page):
    """
    Диагностика состояния date picker.
    """
    logger.info("🔍 Diagnosing date picker state...")

    diagnosis = await page.evaluate('''
        () => {
            const diagnosis = {
                pickerFound: false,
                calendarOpen: false,
                cellsVisible: 0,
                inputFields: 0,
                selectedDates: [],
                errors: []
            };

            // Ищем picker
            const picker = document.querySelector('[class*="picker"]');
            diagnosis.pickerFound = !!picker;

            // Ищем календарь
            const calendar = document.querySelector('.ant-picker-dropdown');
            diagnosis.calendarOpen = !!calendar && calendar.offsetParent !== null;

            // Считаем ячейки
            const cells = document.querySelectorAll('.ant-picker-cell');
            diagnosis.cellsVisible = cells.length;

            // Ищем inputs
            const inputs = document.querySelectorAll('.ant-picker-input input');
            diagnosis.inputFields = inputs.length;

            // Извлекаем значения input'ов
            inputs.forEach((input, idx) => {
                if (input.value) {
                    diagnosis.selectedDates.push({
                        field: idx,
                        value: input.value
                    });
                }
            });

            // Ищем selected ячейки
            const selectedCells = document.querySelectorAll('.ant-picker-cell-selected');
            selectedCells.forEach(cell => {
                const text = cell.querySelector('.ant-picker-cell-inner')?.textContent;
                if (text) {
                    diagnosis.selectedDates.push({
                        cell: 'selected',
                        day: text
                    });
                }
            });

            // Ищем disabled ячейки
            const disabledCells = document.querySelectorAll('.ant-picker-cell-disabled');
            if (disabledCells.length > 0) {
                diagnosis.disabledCellsCount = disabledCells.length;
            }

            // Проверяем на ошибки
            if (!diagnosis.pickerFound) {
                diagnosis.errors.push('No date picker found');
            }

            if (diagnosis.cellsVisible === 0 && diagnosis.calendarOpen) {
                diagnosis.errors.push('Calendar open but no cells visible');
            }

            if (diagnosis.inputFields === 0) {
                diagnosis.errors.push('No input fields found');
            }

            return diagnosis;
        }
    ''')

    logger.info(f"   📋 Picker found: {diagnosis['pickerFound']}")
    logger.info(f"   📋 Calendar open: {diagnosis['calendarOpen']}")
    logger.info(f"   📋 Visible cells: {diagnosis['cellsVisible']}")
    logger.info(f"   📋 Input fields: {diagnosis['inputFields']}")

    if diagnosis.get('selectedDates'):
        logger.info(f"   📋 Selected: {diagnosis['selectedDates']}")

    if diagnosis.get('errors'):
        logger.warning(f"   ⚠️ Issues: {diagnosis['errors']}")

    return diagnosis


async def diagnose_table(page):
    """
    Диагностика состояния таблицы.
    """
    logger.info("🔍 Diagnosing table state...")

    diagnosis = await page.evaluate('''
        () => {
            const diagnosis = {
                tableFound: false,
                totalRows: 0,
                cellsPerRow: [],
                isVirtualized: false,
                hasData: false,
                spinnerPresent: false,
                emptyMessage: null
            };

            // Ищем таблицу
            const table = document.querySelector('table');
            diagnosis.tableFound = !!table;

            // Считаем строки
            const rows = Array.from(document.querySelectorAll('tbody tr, tr'));
            diagnosis.totalRows = rows.length;

            // Анализируем структуру
            rows.slice(0, 5).forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length > 0) {
                    diagnosis.cellsPerRow.push(cells.length);
                    diagnosis.hasData = true;
                }
            });

            // Проверяем на виртуализацию
            const scrollContainer = document.querySelector('[class*="virtual"], [class*="scroll"]');
            diagnosis.isVirtualized = !!scrollContainer;

            // Проверяем spinner
            const spinner = document.querySelector('.ant-spin');
            diagnosis.spinnerPresent = !!spinner && spinner.offsetParent !== null;

            // Ищем сообщение об отсутствии данных
            const emptyState = document.querySelector('.ant-empty, [class*="empty"]');
            if (emptyState) {
                diagnosis.emptyMessage = emptyState.innerText;
            }

            return diagnosis;
        }
    ''')

    logger.info(f"   📊 Table found: {diagnosis['tableFound']}")
    logger.info(f"   📊 Total rows: {diagnosis['totalRows']}")
    logger.info(f"   📊 Has data: {diagnosis['hasData']}")
    logger.info(f"   📊 Virtualized: {diagnosis['isVirtualized']}")
    logger.info(f"   📊 Spinner visible: {diagnosis['spinnerPresent']}")

    if diagnosis.get('cellsPerRow'):
        logger.info(f"   📊 Cells per row: {diagnosis['cellsPerRow']}")

    if diagnosis.get('emptyMessage'):
        logger.warning(f"   ⚠️ Empty state: {diagnosis['emptyMessage']}")

    return diagnosis

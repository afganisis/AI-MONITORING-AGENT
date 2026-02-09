"""
AI REPAIR fix strategies using Fortex TOOL KIT.

Flow:
1. Navigate to driver's log page (already on it after scan)
2. Click "AI REPAIR" button in footer bar
3. Click "TOOL KIT" button
4. Check the appropriate checkboxes for the error type
5. Click "PROCEED"
6. Wait for completion

Each error type maps to a GROUP of checkboxes in TOOL KIT:
- MISSING INTERMEDIATE ERROR → FIX INTERMEDIATE + FIX INTERMEDIATE TIME OFFSET + FIX INTERMEDIATE AFTER MAIN
- NO POWER UP ERROR → FIX NO POWER UP + FIX MISSING POWER UP / SHUT DOWN + FIX NO SHUT DOWN
- NO SHUT DOWN ERROR → FIX NO SHUT DOWN + FIX MISSING POWER UP / SHUT DOWN + FIX NO POWER UP
- TWO IDENTICAL STATUSES ERROR → CLEAR TWIN EVENTS
- DRIVING ORIGIN WARNING → FIX EVENT ORIGIN
"""

import time
from typing import List
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


# Mapping: error_key → list of checkbox labels to select in TOOL KIT
AI_REPAIR_CHECKBOX_MAP = {
    "missingIntermediateError": [
        "FIX INTERMEDIATE",
        "FIX INTERMEDIATE TIME OFFSET",
        "FIX INTERMEDIATE AFTER MAIN",
    ],
    "noPowerUpError": [
        "FIX NO POWER UP",
        "FIX MISSING POWER UP / SHUT DOWN",
        "FIX NO SHUT DOWN",
    ],
    "noShutdownError": [
        "FIX NO SHUT DOWN",
        "FIX MISSING POWER UP / SHUT DOWN",
        "FIX NO POWER UP",
    ],
    "twoIdenticalStatusesError": [
        "CLEAR TWIN EVENTS",
    ],
    "drivingOriginWarning": [
        "FIX EVENT ORIGIN",
    ],
}


class AIRepairBaseStrategy(BaseFixStrategy):
    """
    Base strategy for all AI REPAIR fixes via Fortex TOOL KIT.

    Subclasses only need to define error_key and strategy_name.
    The actual automation logic (AI REPAIR → TOOL KIT → checkboxes → PROCEED)
    is shared across all AI REPAIR error types.
    """

    @property
    def checkboxes(self) -> List[str]:
        """Checkbox labels to select in TOOL KIT for this error type."""
        return AI_REPAIR_CHECKBOX_MAP.get(self.error_key, [])

    async def can_handle(self, error) -> bool:
        return error.error_key == self.error_key

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"[AI REPAIR] Fixing '{self.error_key}' for driver {error.driver_id}")
            logger.info(f"[AI REPAIR] Checkboxes to select: {self.checkboxes}")

            # 1. Ensure logged in
            await browser_manager.ensure_logged_in()

            # 2. Click "AI REPAIR" button in footer bar
            logger.info("[AI REPAIR] Step 1: Clicking AI REPAIR button...")
            ai_repair_clicked = await self._click_ai_repair(page, actions)
            if not ai_repair_clicked:
                screenshot = await actions.capture_screenshot(f"ai_repair_button_not_found_{error.id}")
                return FixResult(
                    success=False,
                    message="AI REPAIR button not found in footer",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # 3. Click "TOOL KIT" button
            logger.info("[AI REPAIR] Step 2: Clicking TOOL KIT button...")
            toolkit_clicked = await self._click_toolkit(page, actions)
            if not toolkit_clicked:
                screenshot = await actions.capture_screenshot(f"toolkit_button_not_found_{error.id}")
                return FixResult(
                    success=False,
                    message="TOOL KIT button not found after AI REPAIR",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # 4. Select checkboxes
            logger.info(f"[AI REPAIR] Step 3: Selecting {len(self.checkboxes)} checkboxes...")
            selected_count = await self._select_checkboxes(page, actions)
            logger.info(f"[AI REPAIR] Selected {selected_count}/{len(self.checkboxes)} checkboxes")

            if selected_count == 0:
                screenshot = await actions.capture_screenshot(f"no_checkboxes_selected_{error.id}")
                return FixResult(
                    success=False,
                    message=f"Could not select any checkboxes: {self.checkboxes}",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # 5. Click "PROCEED"
            logger.info("[AI REPAIR] Step 4: Clicking PROCEED...")
            proceed_clicked = await self._click_proceed(page, actions)
            if not proceed_clicked:
                screenshot = await actions.capture_screenshot(f"proceed_button_not_found_{error.id}")
                return FixResult(
                    success=False,
                    message="PROCEED button not found",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # 6. Wait for completion
            logger.info("[AI REPAIR] Step 5: Waiting for AI REPAIR to complete...")
            await page.wait_for_timeout(5000)

            # Take success screenshot
            screenshot = await actions.capture_screenshot(f"ai_repair_success_{self.error_key}_{error.id}")

            elapsed = int((time.time() - start_time) * 1000)
            logger.info(f"[AI REPAIR] Fix completed in {elapsed}ms")

            return FixResult(
                success=True,
                message=f"AI REPAIR completed: selected {selected_count} fixes ({', '.join(self.checkboxes)})",
                execution_time_ms=elapsed,
                screenshot_path=str(screenshot) if screenshot else None,
                metadata={
                    "checkboxes_selected": self.checkboxes,
                    "selected_count": selected_count,
                    "error_key": self.error_key,
                }
            )

        except Exception as e:
            logger.exception(f"[AI REPAIR] Failed for {self.error_key}: {e}")
            screenshot = await actions.capture_screenshot(f"ai_repair_exception_{self.error_key}_{error.id}")

            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

    async def _click_ai_repair(self, page, actions: PlaywrightActions) -> bool:
        """Click the AI REPAIR button in the footer bar."""
        # Try multiple selectors for AI REPAIR button
        selectors = [
            'button:has-text("AI REPAIR")',
            'button span:has-text("AI REPAIR")',
            '.ant-btn:has-text("AI REPAIR")',
        ]

        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000, state='visible')
                if button:
                    # Use coordinate click for reliability (Ant Design buttons can be stubborn)
                    box = await button.bounding_box()
                    if box:
                        await page.mouse.click(
                            box['x'] + box['width'] / 2,
                            box['y'] + box['height'] / 2
                        )
                    else:
                        await button.click(force=True)

                    logger.info("[AI REPAIR] AI REPAIR button clicked")
                    await page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue

        logger.error("[AI REPAIR] AI REPAIR button not found with any selector")
        return False

    async def _click_toolkit(self, page, actions: PlaywrightActions) -> bool:
        """Click the TOOL KIT button that appears after AI REPAIR."""
        selectors = [
            'button:has-text("TOOL KIT")',
            'button span:has-text("TOOL KIT")',
            '.ant-btn:has-text("TOOL KIT")',
        ]

        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000, state='visible')
                if button:
                    box = await button.bounding_box()
                    if box:
                        await page.mouse.click(
                            box['x'] + box['width'] / 2,
                            box['y'] + box['height'] / 2
                        )
                    else:
                        await button.click(force=True)

                    logger.info("[AI REPAIR] TOOL KIT button clicked")
                    await page.wait_for_timeout(2000)
                    return True
            except Exception:
                continue

        logger.error("[AI REPAIR] TOOL KIT button not found")
        return False

    async def _select_checkboxes(self, page, actions: PlaywrightActions) -> int:
        """Select the appropriate checkboxes in the TOOL KIT panel."""
        selected_count = 0

        # First, click CLEAR to uncheck all defaults
        try:
            clear_btn = await page.wait_for_selector('button:has-text("CLEAR"), span:has-text("CLEAR")', timeout=3000)
            if clear_btn:
                await clear_btn.click(force=True)
                await page.wait_for_timeout(500)
                logger.info("[AI REPAIR] Cleared all checkboxes first")
        except Exception:
            logger.warning("[AI REPAIR] CLEAR button not found, proceeding with current state")

        # Now select the checkboxes we need
        for checkbox_label in self.checkboxes:
            try:
                # Find checkbox by its label text using JavaScript
                # The TOOL KIT panel has checkboxes with text labels
                checked = await page.evaluate(f'''
                    (labelText) => {{
                        // Find all checkbox containers
                        const labels = document.querySelectorAll('.ant-checkbox-wrapper, label');
                        for (const label of labels) {{
                            const text = label.textContent?.trim().toUpperCase() || '';
                            if (text === labelText.toUpperCase() || text.includes(labelText.toUpperCase())) {{
                                // Find the checkbox input or the wrapper
                                const checkbox = label.querySelector('input[type="checkbox"]') || label.querySelector('.ant-checkbox');
                                const wrapper = label.querySelector('.ant-checkbox-wrapper') || label;

                                // Check if already checked
                                const isChecked = label.classList.contains('ant-checkbox-wrapper-checked') ||
                                                  checkbox?.checked ||
                                                  label.querySelector('.ant-checkbox-checked');

                                if (!isChecked) {{
                                    // Click the label to toggle checkbox
                                    label.click();
                                    return true;
                                }} else {{
                                    return true;  // Already checked
                                }}
                            }}
                        }}
                        return false;
                    }}
                ''', checkbox_label)

                if checked:
                    selected_count += 1
                    logger.info(f"[AI REPAIR] Checkbox selected: '{checkbox_label}'")
                else:
                    logger.warning(f"[AI REPAIR] Checkbox NOT found: '{checkbox_label}'")

                await page.wait_for_timeout(300)

            except Exception as e:
                logger.error(f"[AI REPAIR] Error selecting checkbox '{checkbox_label}': {e}")

        return selected_count

    async def _click_proceed(self, page, actions: PlaywrightActions) -> bool:
        """Click the PROCEED button to execute the selected fixes."""
        selectors = [
            'button:has-text("PROCEED")',
            'button span:has-text("PROCEED")',
            '.ant-btn:has-text("PROCEED")',
        ]

        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000, state='visible')
                if button:
                    box = await button.bounding_box()
                    if box:
                        await page.mouse.click(
                            box['x'] + box['width'] / 2,
                            box['y'] + box['height'] / 2
                        )
                    else:
                        await button.click(force=True)

                    logger.info("[AI REPAIR] PROCEED button clicked")
                    await page.wait_for_timeout(3000)
                    return True
            except Exception:
                continue

        logger.error("[AI REPAIR] PROCEED button not found")
        return False


# ============================================================================
# Concrete strategies for each AI REPAIR error type
# ============================================================================

class MissingIntermediateFixStrategy(AIRepairBaseStrategy):
    """Fix MISSING INTERMEDIATE ERROR via AI REPAIR TOOL KIT."""

    @property
    def error_key(self) -> str:
        return "missingIntermediateError"

    @property
    def strategy_name(self) -> str:
        return "AI REPAIR: Fix Missing Intermediate"


class NoPowerUpAIRepairStrategy(AIRepairBaseStrategy):
    """Fix NO POWER UP ERROR via AI REPAIR TOOL KIT."""

    @property
    def error_key(self) -> str:
        return "noPowerUpError"

    @property
    def strategy_name(self) -> str:
        return "AI REPAIR: Fix No Power Up"


class NoShutdownAIRepairStrategy(AIRepairBaseStrategy):
    """Fix NO SHUT DOWN ERROR via AI REPAIR TOOL KIT."""

    @property
    def error_key(self) -> str:
        return "noShutdownError"

    @property
    def strategy_name(self) -> str:
        return "AI REPAIR: Fix No Shutdown"


class TwoIdenticalStatusesFixStrategy(AIRepairBaseStrategy):
    """Fix TWO IDENTICAL STATUSES ERROR via AI REPAIR TOOL KIT."""

    @property
    def error_key(self) -> str:
        return "twoIdenticalStatusesError"

    @property
    def strategy_name(self) -> str:
        return "AI REPAIR: Clear Twin Events"


class DrivingOriginFixStrategy(AIRepairBaseStrategy):
    """Fix DRIVING ORIGIN WARNING via AI REPAIR TOOL KIT."""

    @property
    def error_key(self) -> str:
        return "drivingOriginWarning"

    @property
    def strategy_name(self) -> str:
        return "AI REPAIR: Fix Event Origin"

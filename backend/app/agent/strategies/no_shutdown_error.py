"""
Fix strategy for noShutdownError errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class NoShutdownErrorFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'noShutdownError' errors.

    Fix approach:
    - Navigate to event edit page
    - Add missing shutdown event
    - Submit changes
    """

    @property
    def error_key(self) -> str:
        return "noShutdownError"

    @property
    def strategy_name(self) -> str:
        return "Add Missing Shutdown Event"

    async def can_handle(self, error) -> bool:
        return error.error_key == "noShutdownError"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing no shutdown error for driver {error.driver_id}")

            await browser_manager.ensure_logged_in()

            # Navigate to log edit page
            log_url = f"{browser_manager.login_url.rstrip('/')}/logs/{error.log_id or error.driver_id}"
            await page.goto(log_url, wait_until="networkidle")

            # Click "Add Event" or "Add Shutdown" button
            add_clicked = await actions.click("button:has-text('Add Event'), button:has-text('Add Shutdown')")

            if not add_clicked:
                screenshot = await actions.capture_screenshot(f"no_shutdown_no_button_{error.id}")
                return FixResult(
                    success=False,
                    message="Could not find add event button",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # Select event type "Shutdown" or similar
            await actions.select_option("select[name='eventType']", label="Shutdown")

            # Fill timestamp if needed
            # await actions.fill("input[name='timestamp']", "value")

            # Submit
            submit_clicked = await actions.click("button[type='submit'], button:has-text('Save')")

            if not submit_clicked:
                screenshot = await actions.capture_screenshot(f"no_shutdown_no_submit_{error.id}")
                return FixResult(
                    success=False,
                    message="Could not submit shutdown event",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # Verify success
            success, message = await actions.verify_success(
                success_selector=".toast-success, .alert-success",
                error_selector=".toast-error, .alert-error",
                timeout=5000
            )

            screenshot = await actions.capture_screenshot(
                f"no_shutdown_{'success' if success else 'failed'}_{error.id}"
            )

            return FixResult(
                success=success,
                message=message or "Shutdown event added",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

        except Exception as e:
            logger.exception(f"NoShutdownErrorFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(f"no_shutdown_exception_{error.id}")
            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

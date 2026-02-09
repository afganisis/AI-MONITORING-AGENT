"""
Fix strategy for noPowerUpError errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class NoPowerUpErrorFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'noPowerUpError' errors.

    Similar to NoShutdownError - adds missing power-up event.
    """

    @property
    def error_key(self) -> str:
        return "noPowerUpError"

    @property
    def strategy_name(self) -> str:
        return "Add Missing Power-Up Event"

    async def can_handle(self, error) -> bool:
        return error.error_key == "noPowerUpError"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing no power-up error for driver {error.driver_id}")

            await browser_manager.ensure_logged_in()

            log_url = f"{browser_manager.login_url.rstrip('/')}/logs/{error.log_id or error.driver_id}"
            await page.goto(log_url, wait_until="networkidle")

            # Click add event button
            if not await actions.click("button:has-text('Add Event'), button:has-text('Add Power-Up')"):
                screenshot = await actions.capture_screenshot(f"no_powerup_no_button_{error.id}")
                return FixResult(
                    success=False,
                    message="Could not find add event button",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # Select power-up event type
            await actions.select_option("select[name='eventType']", label="Power Up")

            # Submit
            if not await actions.click("button[type='submit'], button:has-text('Save')"):
                screenshot = await actions.capture_screenshot(f"no_powerup_no_submit_{error.id}")
                return FixResult(
                    success=False,
                    message="Could not submit power-up event",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            success, message = await actions.verify_success(
                success_selector=".toast-success, .alert-success",
                error_selector=".toast-error, .alert-error"
            )

            screenshot = await actions.capture_screenshot(
                f"no_powerup_{'success' if success else 'failed'}_{error.id}"
            )

            return FixResult(
                success=success,
                message=message or "Power-up event added",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

        except Exception as e:
            logger.exception(f"NoPowerUpErrorFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(f"no_powerup_exception_{error.id}")
            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

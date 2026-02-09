"""
Fix strategy for excessiveLogInWarning errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class ExcessiveLogInFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'excessiveLogInWarning' errors.

    Fix approach:
    - Navigate to driver logs
    - Remove duplicate login events
    - Keep only first login event
    """

    @property
    def error_key(self) -> str:
        return "excessiveLogInWarning"

    @property
    def strategy_name(self) -> str:
        return "Remove Excessive Login Events"

    async def can_handle(self, error) -> bool:
        return error.error_key == "excessiveLogInWarning"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing excessive login warning for driver {error.driver_id}")

            await browser_manager.ensure_logged_in()

            log_url = f"{browser_manager.login_url.rstrip('/')}/logs/{error.log_id or error.driver_id}"
            await page.goto(log_url, wait_until="networkidle")

            # Find all login events
            login_events_selector = "tr[data-event-type='login'], .event-login"
            event_count = await actions.count_elements(login_events_selector)

            if event_count <= 1:
                return FixResult(
                    success=True,
                    message="No excessive logins found",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # Delete all but first login event
            deleted_count = 0
            for i in range(1, event_count):  # Start from second event
                delete_selector = f"{login_events_selector}:nth-child({i+1}) button.delete, {login_events_selector}:nth-child({i+1}) button:has-text('Delete')"

                if await actions.click(delete_selector, timeout=2000):
                    # Confirm deletion if needed
                    await actions.click("button:has-text('Confirm'), button:has-text('Yes')", timeout=2000)
                    deleted_count += 1

            success = deleted_count > 0
            message = f"Deleted {deleted_count} excessive login events"

            screenshot = await actions.capture_screenshot(
                f"excessive_login_{'success' if success else 'failed'}_{error.id}"
            )

            return FixResult(
                success=success,
                message=message,
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None,
                metadata={"deleted_count": deleted_count}
            )

        except Exception as e:
            logger.exception(f"ExcessiveLogInFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(f"excessive_login_exception_{error.id}")
            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

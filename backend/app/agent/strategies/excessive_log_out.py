"""
Fix strategy for excessiveLogOutWarning errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class ExcessiveLogOutFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'excessiveLogOutWarning' errors.

    Similar to ExcessiveLogIn - removes duplicate logout events.
    """

    @property
    def error_key(self) -> str:
        return "excessiveLogOutWarning"

    @property
    def strategy_name(self) -> str:
        return "Remove Excessive Logout Events"

    async def can_handle(self, error) -> bool:
        return error.error_key == "excessiveLogOutWarning"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing excessive logout warning for driver {error.driver_id}")

            await browser_manager.ensure_logged_in()

            log_url = f"{browser_manager.login_url.rstrip('/')}/logs/{error.log_id or error.driver_id}"
            await page.goto(log_url, wait_until="networkidle")

            # Find all logout events
            logout_events_selector = "tr[data-event-type='logout'], .event-logout"
            event_count = await actions.count_elements(logout_events_selector)

            if event_count <= 1:
                return FixResult(
                    success=True,
                    message="No excessive logouts found",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # Delete all but last logout event
            deleted_count = 0
            for i in range(event_count - 1):  # Keep last logout
                delete_selector = f"{logout_events_selector}:nth-child({i+1}) button.delete, {logout_events_selector}:nth-child({i+1}) button:has-text('Delete')"

                if await actions.click(delete_selector, timeout=2000):
                    await actions.click("button:has-text('Confirm'), button:has-text('Yes')", timeout=2000)
                    deleted_count += 1

            success = deleted_count > 0
            message = f"Deleted {deleted_count} excessive logout events"

            screenshot = await actions.capture_screenshot(
                f"excessive_logout_{'success' if success else 'failed'}_{error.id}"
            )

            return FixResult(
                success=success,
                message=message,
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None,
                metadata={"deleted_count": deleted_count}
            )

        except Exception as e:
            logger.exception(f"ExcessiveLogOutFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(f"excessive_logout_exception_{error.id}")
            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

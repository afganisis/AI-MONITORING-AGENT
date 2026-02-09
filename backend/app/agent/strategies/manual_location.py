"""
Fix strategy for eventHasManualLocation errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class ManualLocationFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'eventHasManualLocation' errors.

    Fix approach:
    - Navigate to event edit page
    - Replace manual location with GPS location
    - Or mark as acceptable manual entry
    """

    @property
    def error_key(self) -> str:
        return "eventHasManualLocation"

    @property
    def strategy_name(self) -> str:
        return "Fix Manual Location Entry"

    async def can_handle(self, error) -> bool:
        return error.error_key == "eventHasManualLocation"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing manual location error for event {error.event_id}")

            await browser_manager.ensure_logged_in()

            event_url = f"{browser_manager.login_url.rstrip('/')}/events/{error.event_id}/edit"
            await page.goto(event_url, wait_until="networkidle")

            # Try to click "Use GPS Location" button
            gps_clicked = await actions.click(
                "button:has-text('Use GPS'), button:has-text('Auto-detect Location')",
                timeout=3000
            )

            if gps_clicked:
                # Submit changes
                if await actions.click("button[type='submit'], button:has-text('Save')"):
                    success, message = await actions.verify_success(
                        success_selector=".toast-success, .alert-success",
                        error_selector=".toast-error, .alert-error"
                    )

                    screenshot = await actions.capture_screenshot(
                        f"manual_location_gps_{'success' if success else 'failed'}_{error.id}"
                    )

                    return FixResult(
                        success=success,
                        message=message or "Switched to GPS location",
                        execution_time_ms=int((time.time() - start_time) * 1000),
                        screenshot_path=str(screenshot) if screenshot else None
                    )

            # Alternative: Mark as acceptable manual entry
            accept_clicked = await actions.click(
                "button:has-text('Accept'), button:has-text('Mark as Valid')",
                timeout=3000
            )

            if accept_clicked:
                success, message = await actions.verify_success(
                    success_selector=".toast-success, .alert-success",
                    error_selector=".toast-error, .alert-error"
                )

                screenshot = await actions.capture_screenshot(
                    f"manual_location_accepted_{error.id}"
                )

                return FixResult(
                    success=success,
                    message=message or "Manual location marked as valid",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # Could not fix
            screenshot = await actions.capture_screenshot(f"manual_location_no_action_{error.id}")
            return FixResult(
                success=False,
                message="No fix action available for manual location",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

        except Exception as e:
            logger.exception(f"ManualLocationFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(f"manual_location_exception_{error.id}")
            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

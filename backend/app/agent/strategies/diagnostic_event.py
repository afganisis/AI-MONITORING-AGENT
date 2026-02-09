"""
Fix strategy for diagnosticEvent errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class DiagnosticEventFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'diagnosticEvent' errors.

    Fix approach:
    - Navigate to driver's diagnostic events page
    - Click 'Acknowledge' or 'Clear' button for the event
    - Verify event is cleared
    """

    @property
    def error_key(self) -> str:
        return "diagnosticEvent"

    @property
    def strategy_name(self) -> str:
        return "Acknowledge Diagnostic Event"

    async def can_handle(self, error) -> bool:
        return error.error_key == "diagnosticEvent"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing diagnostic event for driver {error.driver_id}")

            # Ensure logged in
            await browser_manager.ensure_logged_in()

            # Navigate to diagnostics page
            diagnostics_url = f"{browser_manager.login_url.rstrip('/')}/diagnostics/{error.driver_id}"
            await page.goto(diagnostics_url, wait_until="networkidle")

            # Find and click acknowledge button for this event
            # Try multiple selector patterns
            selectors = [
                f"button[data-event-id='{error.event_id}']",
                f"tr[data-event-id='{error.event_id}'] button.acknowledge",
                f"tr[data-event-id='{error.event_id}'] button:has-text('Acknowledge')",
                "button:has-text('Acknowledge')",  # Fallback to first acknowledge button
            ]

            clicked = False
            for selector in selectors:
                if await actions.click(selector, timeout=3000):
                    clicked = True
                    break

            if not clicked:
                screenshot = await actions.capture_screenshot(
                    f"diagnostic_event_no_button_{error.id}"
                )
                return FixResult(
                    success=False,
                    message="Could not find acknowledge button",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # Wait for confirmation
            success, message = await actions.verify_success(
                success_selector=".toast-success, .alert-success, .notification-success",
                error_selector=".toast-error, .alert-error, .notification-error",
                timeout=5000
            )

            # Capture screenshot
            screenshot = await actions.capture_screenshot(
                f"diagnostic_event_{'success' if success else 'failed'}_{error.id}"
            )

            execution_time = int((time.time() - start_time) * 1000)

            return FixResult(
                success=success,
                message=message or "Diagnostic event acknowledged",
                execution_time_ms=execution_time,
                screenshot_path=str(screenshot) if screenshot else None
            )

        except Exception as e:
            logger.exception(f"DiagnosticEventFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(
                f"diagnostic_event_exception_{error.id}"
            )

            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

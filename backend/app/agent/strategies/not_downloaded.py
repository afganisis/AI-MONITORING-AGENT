"""
Fix strategy for eventIsNotDownloaded errors.
"""

import time
from loguru import logger
from .base import BaseFixStrategy, FixResult
from ...playwright.actions import PlaywrightActions


class NotDownloadedFixStrategy(BaseFixStrategy):
    """
    Strategy for fixing 'eventIsNotDownloaded' errors.

    Fix approach:
    - Navigate to event sync page
    - Trigger re-sync or download from device
    - Wait for sync completion
    """

    @property
    def error_key(self) -> str:
        return "eventIsNotDownloaded"

    @property
    def strategy_name(self) -> str:
        return "Re-sync Event from Device"

    async def can_handle(self, error) -> bool:
        return error.error_key == "eventIsNotDownloaded"

    async def execute(self, error, fix, browser_manager) -> FixResult:
        start_time = time.time()
        page = browser_manager.page
        actions = PlaywrightActions(page, browser_manager.screenshot_dir)

        try:
            logger.info(f"Fixing not downloaded error for event {error.event_id}")

            await browser_manager.ensure_logged_in()

            # Navigate to driver sync page
            sync_url = f"{browser_manager.login_url.rstrip('/')}/drivers/{error.driver_id}/sync"
            await page.goto(sync_url, wait_until="networkidle")

            # Click "Sync Now" or "Download Events" button
            sync_clicked = await actions.click(
                "button:has-text('Sync Now'), button:has-text('Download Events'), button:has-text('Re-sync')",
                timeout=5000
            )

            if not sync_clicked:
                screenshot = await actions.capture_screenshot(f"not_downloaded_no_button_{error.id}")
                return FixResult(
                    success=False,
                    message="Could not find sync button",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    screenshot_path=str(screenshot) if screenshot else None
                )

            # Wait for sync to complete (longer timeout)
            success, message = await actions.verify_success(
                success_selector=".sync-complete, .toast-success, .alert-success",
                error_selector=".sync-failed, .toast-error, .alert-error",
                timeout=30000  # 30 seconds for sync
            )

            screenshot = await actions.capture_screenshot(
                f"not_downloaded_{'success' if success else 'failed'}_{error.id}"
            )

            return FixResult(
                success=success,
                message=message or "Event re-synced from device",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

        except Exception as e:
            logger.exception(f"NotDownloadedFixStrategy failed: {e}")
            screenshot = await actions.capture_screenshot(f"not_downloaded_exception_{error.id}")
            return FixResult(
                success=False,
                message=f"Exception: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
                screenshot_path=str(screenshot) if screenshot else None
            )

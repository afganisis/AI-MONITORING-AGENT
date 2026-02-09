"""
Generic UI interaction wrappers with error handling and retry logic.
"""

import asyncio
from typing import Optional, Tuple, List
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from loguru import logger


class PlaywrightActions:
    """
    Generic UI interaction wrappers with error handling.

    Features:
    - Retry logic for all actions
    - Automatic screenshot on failures
    - Element visibility verification
    - Success/error message detection
    """

    def __init__(
        self,
        page: Page,
        screenshot_dir: str = "./screenshots"
    ):
        """
        Initialize Playwright Actions.

        Args:
            page: Playwright Page object
            screenshot_dir: Directory to save screenshots
        """
        self.page = page
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int = 5000,
        state: str = "visible"
    ) -> bool:
        """
        Wait for element to appear.

        Args:
            selector: CSS selector
            timeout: Wait timeout in milliseconds
            state: Element state to wait for (visible, attached, hidden, detached)

        Returns:
            True if element found, False otherwise
        """
        try:
            await self.page.wait_for_selector(
                selector,
                timeout=timeout,
                state=state
            )
            return True
        except PlaywrightTimeout:
            logger.warning(f"Timeout waiting for selector: {selector}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for selector {selector}: {e}")
            return False

    async def click(
        self,
        selector: str,
        timeout: int = 5000,
        max_retries: int = 3
    ) -> bool:
        """
        Click element with retry and error capture.

        Args:
            selector: CSS selector
            timeout: Click timeout in milliseconds
            max_retries: Maximum retry attempts

        Returns:
            True if click successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Wait for element to be visible
                if not await self.wait_for_selector(selector, timeout):
                    await self.capture_screenshot(f"click_wait_failed_{selector.replace(' ', '_')}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    return False

                # Click element
                await self.page.click(selector, timeout=timeout)
                logger.debug(f"Clicked: {selector}")
                return True

            except PlaywrightTimeout:
                logger.warning(f"Click timeout on {selector} (attempt {attempt + 1}/{max_retries})")
                await self.capture_screenshot(f"click_timeout_{selector.replace(' ', '_')}")

            except Exception as e:
                logger.error(f"Click failed on {selector}: {e}")
                await self.capture_screenshot(f"click_error_{selector.replace(' ', '_')}")

            # Wait before retry
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return False

    async def fill(
        self,
        selector: str,
        value: str,
        timeout: int = 5000,
        max_retries: int = 3
    ) -> bool:
        """
        Fill input field with retry.

        Args:
            selector: CSS selector
            value: Text to fill
            timeout: Fill timeout in milliseconds
            max_retries: Maximum retry attempts

        Returns:
            True if fill successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Wait for element
                if not await self.wait_for_selector(selector, timeout):
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    return False

                # Clear and fill
                await self.page.fill(selector, value, timeout=timeout)
                logger.debug(f"Filled {selector} with: {value}")
                return True

            except Exception as e:
                logger.error(f"Fill failed on {selector}: {e}")
                await self.capture_screenshot(f"fill_error_{selector.replace(' ', '_')}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return False

    async def select_option(
        self,
        selector: str,
        value: str = None,
        label: str = None,
        timeout: int = 5000
    ) -> bool:
        """
        Select dropdown option.

        Args:
            selector: CSS selector for select element
            value: Option value to select
            label: Option label to select (alternative to value)
            timeout: Select timeout in milliseconds

        Returns:
            True if selection successful, False otherwise
        """
        try:
            # Wait for element
            if not await self.wait_for_selector(selector, timeout):
                return False

            # Select by value or label
            if value:
                await self.page.select_option(selector, value=value, timeout=timeout)
            elif label:
                await self.page.select_option(selector, label=label, timeout=timeout)
            else:
                logger.error("Must provide either value or label for select_option")
                return False

            logger.debug(f"Selected option in {selector}")
            return True

        except Exception as e:
            logger.error(f"Select option failed on {selector}: {e}")
            await self.capture_screenshot(f"select_error_{selector.replace(' ', '_')}")
            return False

    async def get_text(
        self,
        selector: str,
        timeout: int = 5000
    ) -> Optional[str]:
        """
        Get text content from element.

        Args:
            selector: CSS selector
            timeout: Wait timeout in milliseconds

        Returns:
            Element text content or None if failed
        """
        try:
            if not await self.wait_for_selector(selector, timeout):
                return None

            text = await self.page.text_content(selector, timeout=timeout)
            return text.strip() if text else None

        except Exception as e:
            logger.error(f"Get text failed on {selector}: {e}")
            return None

    async def verify_success(
        self,
        success_selector: str = None,
        error_selector: str = None,
        timeout: int = 10000
    ) -> Tuple[bool, str]:
        """
        Verify action success by checking for success/error messages.

        Args:
            success_selector: CSS selector for success message
            error_selector: CSS selector for error message
            timeout: Wait timeout in milliseconds

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Wait for either success or error message
            selectors = []
            if success_selector:
                selectors.append(success_selector)
            if error_selector:
                selectors.append(error_selector)

            if not selectors:
                return True, "No verification selectors provided"

            # Wait for any of the selectors
            found_selector = None
            for selector in selectors:
                if await self.wait_for_selector(selector, timeout=timeout // len(selectors)):
                    found_selector = selector
                    break

            if not found_selector:
                logger.warning("No success/error message found")
                return False, "No confirmation message appeared"

            # Get message text
            message_text = await self.get_text(found_selector)

            # Determine success/failure
            is_success = found_selector == success_selector
            logger.info(f"Verification result: {'Success' if is_success else 'Error'} - {message_text}")

            return is_success, message_text or ""

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False, f"Verification error: {str(e)}"

    async def wait_for_navigation(
        self,
        url_pattern: str = None,
        timeout: int = 30000
    ) -> bool:
        """
        Wait for page navigation.

        Args:
            url_pattern: URL pattern to wait for (glob pattern)
            timeout: Wait timeout in milliseconds

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            if url_pattern:
                await self.page.wait_for_url(url_pattern, timeout=timeout)
            else:
                await self.page.wait_for_load_state("networkidle", timeout=timeout)

            logger.debug(f"Navigation complete, current URL: {self.page.url}")
            return True

        except PlaywrightTimeout:
            logger.warning(f"Navigation timeout (pattern: {url_pattern})")
            return False
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def capture_screenshot(self, name: str) -> Optional[Path]:
        """
        Save screenshot with timestamp.

        Args:
            name: Base name for screenshot file

        Returns:
            Path to saved screenshot or None if failed
        """
        from datetime import datetime

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshot_dir / filename

            await self.page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    async def is_visible(self, selector: str) -> bool:
        """
        Check if element is visible.

        Args:
            selector: CSS selector

        Returns:
            True if visible, False otherwise
        """
        try:
            return await self.page.is_visible(selector)
        except:
            return False

    async def count_elements(self, selector: str) -> int:
        """
        Count elements matching selector.

        Args:
            selector: CSS selector

        Returns:
            Number of matching elements
        """
        try:
            elements = await self.page.query_selector_all(selector)
            return len(elements)
        except:
            return 0

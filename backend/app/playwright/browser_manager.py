"""
Browser lifecycle management with session persistence.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright
)
from loguru import logger


class SessionExpiredError(Exception):
    """Raised when browser session has expired and needs re-authentication."""
    pass


class BrowserManager:
    """
    Manages Playwright browser lifecycle and session persistence.

    Features:
    - Single persistent browser context
    - Session cookie management
    - Login state persistence across restarts
    - Headless/headful mode toggle
    - Screenshot capture on errors
    """

    def __init__(
        self,
        headless: bool = True,
        user_data_dir: str = "./playwright_data",
        screenshot_dir: str = "./screenshots"
    ):
        """
        Initialize Browser Manager.

        Args:
            headless: Run browser in headless mode
            user_data_dir: Directory to store session data
            screenshot_dir: Directory to save screenshots
        """
        self.headless = headless
        self.user_data_dir = Path(user_data_dir)
        self.screenshot_dir = Path(screenshot_dir)
        self.session_file = self.user_data_dir / "session_state.json"

        # Create directories
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Playwright objects
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Login credentials (set via login method)
        self.login_url: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def initialize(self) -> None:
        """
        Start Playwright and create browser context.
        Loads existing session if available.
        """
        try:
            logger.info(f"Initializing Playwright (headless={self.headless})")

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-notifications",  # Disable browser notifications
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-sync",
                    "--no-default-browser-check",
                    "--disable-popup-blocking",  # Allow popups from our automation
                    "--disable-infobars",  # Disable infobars
                    "--disable-blink-features=AutomationControlled",  # Hide automation
                    "--disable-web-security",  # Disable CORS (for localhost)
                    "--disable-features=IsolateOrigins,site-per-process",  # Disable origin isolation
                    "--allow-running-insecure-content",  # Allow localhost
                    "--disable-site-isolation-trials",  # Disable site isolation
                    "--no-first-run",  # Skip first run wizards
                    "--no-service-autorun",  # Don't autorun services
                    "--password-store=basic",  # Use basic password store
                    "--use-mock-keychain",  # Use mock keychain (no OS prompts)
                ]
            )

            # Load persistent context (preserves cookies/session)
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "accept_downloads": True,  # Allow downloads without prompts
                "bypass_csp": True,  # Bypass Content Security Policy
                "ignore_https_errors": True,  # Ignore HTTPS errors for localhost
            }

            if self.session_file.exists():
                logger.info("Loading existing session state")
                context_options["storage_state"] = str(self.session_file)

            self.context = await self.browser.new_context(**context_options)

            self.page = await self.context.new_page()

            logger.info("Playwright initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize Playwright: {e}")
            await self.cleanup()
            raise

    async def login(
        self,
        url: str,
        username: str,
        password: str,
        username_selector: str = "input[name='username']",
        password_selector: str = "input[name='password']",
        submit_selector: str = "button[type='submit']",
        success_url_pattern: str = "**/dashboard**"
    ) -> bool:
        """
        Login to Fortex UI and save session.

        Args:
            url: Login page URL
            username: Username credential
            password: Password credential
            username_selector: CSS selector for username input
            password_selector: CSS selector for password input
            submit_selector: CSS selector for submit button
            success_url_pattern: URL pattern to wait for after login

        Returns:
            True if login successful, False otherwise
        """
        try:
            logger.info(f"Logging in to {url}")

            # Save credentials for re-login
            self.login_url = url
            self.username = username
            self.password = password

            # Navigate to login page
            await self.page.goto(url, wait_until="networkidle")

            # Fill credentials
            await self.page.fill(username_selector, username)
            await self.page.fill(password_selector, password)

            # Click submit
            await self.page.click(submit_selector)

            # Wait for redirect to dashboard
            await self.page.wait_for_url(success_url_pattern, timeout=15000)

            # Save session cookies
            await self.context.storage_state(path=str(self.session_file))

            logger.info("Login successful, session saved")
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            await self.capture_screenshot("login_failed")
            return False

    async def is_logged_in(self, dashboard_url: str = None) -> bool:
        """
        Check if session is still valid.

        Args:
            dashboard_url: URL to check for logged-in state (optional)

        Returns:
            True if logged in, False otherwise
        """
        try:
            if not dashboard_url:
                return True  # Can't verify without URL

            # Try to navigate to dashboard
            response = await self.page.goto(dashboard_url, wait_until="domcontentloaded", timeout=5000)

            # Check if redirected to login
            if "login" in self.page.url.lower():
                logger.warning("Session expired, redirected to login")
                return False

            return True

        except Exception as e:
            logger.warning(f"Session check failed: {e}")
            return False

    async def ensure_logged_in(self) -> None:
        """
        Ensure valid session, re-login if needed.

        Raises:
            SessionExpiredError: If re-login fails
        """
        if not await self.is_logged_in():
            logger.info("Session expired, attempting re-login")

            if not self.username or not self.password or not self.login_url:
                raise SessionExpiredError("No login credentials stored for re-authentication")

            success = await self.login(
                self.login_url,
                self.username,
                self.password
            )

            if not success:
                raise SessionExpiredError("Re-login failed")

    async def capture_screenshot(self, name: str) -> Path:
        """
        Save screenshot with timestamp.

        Args:
            name: Base name for screenshot file

        Returns:
            Path to saved screenshot
        """
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshot_dir / filename

        try:
            await self.page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    async def cleanup(self) -> None:
        """Close browser and cleanup resources."""
        try:
            logger.info("Cleaning up Playwright resources")

            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()

            logger.info("Playwright cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

"""
Base class for all fix strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from loguru import logger
import asyncio
import time


class FixResult(BaseModel):
    """Result of fix execution"""
    success: bool
    message: str
    execution_time_ms: int
    screenshot_path: Optional[str] = None
    metadata: Optional[dict] = None


class BaseFixStrategy(ABC):
    """
    Abstract base class for all fix strategies.

    Each strategy implements the logic to fix a specific error type
    via Playwright browser automation.
    """

    @property
    @abstractmethod
    def error_key(self) -> str:
        """Error key this strategy handles (e.g., 'diagnosticEvent')"""
        pass

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Human-readable strategy name"""
        pass

    @abstractmethod
    async def can_handle(self, error) -> bool:
        """
        Check if this strategy can handle the error.

        Args:
            error: Error model instance

        Returns:
            True if strategy can handle this error
        """
        pass

    @abstractmethod
    async def execute(self, error, fix, browser_manager) -> FixResult:
        """
        Execute the fix automation.

        Args:
            error: Error model instance
            fix: Fix model instance
            browser_manager: BrowserManager instance

        Returns:
            FixResult with success status and details
        """
        pass

    async def verify(self, error, browser_manager) -> bool:
        """
        Verify the fix was successful (optional).

        Args:
            error: Error model instance
            browser_manager: BrowserManager instance

        Returns:
            True if fix verified successful
        """
        # Default implementation - override if needed
        return True

    async def retry(
        self,
        error,
        fix,
        browser_manager,
        max_retries: int = 3
    ) -> FixResult:
        """
        Retry logic with exponential backoff.

        Args:
            error: Error model instance
            fix: Fix model instance
            browser_manager: BrowserManager instance
            max_retries: Maximum number of retry attempts

        Returns:
            FixResult from successful attempt or final failure
        """
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Executing {self.strategy_name} for error {error.id} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )

                result = await self.execute(error, fix, browser_manager)

                if result.success:
                    logger.info(f"Fix successful on attempt {attempt + 1}")
                    return result

                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Fix failed, retrying in {wait_time}s... "
                        f"(message: {result.message})"
                    )
                    await asyncio.sleep(wait_time)

            except Exception as e:
                logger.exception(f"Attempt {attempt + 1} raised exception: {e}")

                if attempt == max_retries - 1:
                    return FixResult(
                        success=False,
                        message=f"Exception after {max_retries} attempts: {str(e)}",
                        execution_time_ms=0
                    )

                await asyncio.sleep(2 ** attempt)

        return FixResult(
            success=False,
            message=f"Max retries ({max_retries}) exceeded",
            execution_time_ms=0
        )

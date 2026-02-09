"""
Registry of all fix strategies.
"""

from typing import Dict, Optional, List
from loguru import logger

from .base import BaseFixStrategy


class StrategyRegistry:
    """
    Central registry for all fix strategies.

    Provides strategy lookup by error key and
    manages strategy lifecycle.
    """

    def __init__(self):
        self.strategies: Dict[str, BaseFixStrategy] = {}
        self._initialized = False

    def register(self, strategy: BaseFixStrategy) -> None:
        """
        Register a fix strategy.

        Args:
            strategy: Strategy instance to register
        """
        error_key = strategy.error_key

        if error_key in self.strategies:
            logger.warning(
                f"Strategy for '{error_key}' already registered, overwriting"
            )

        self.strategies[error_key] = strategy
        logger.debug(f"Registered strategy: {strategy.strategy_name} ({error_key})")

    def get_strategy(self, error_key: str) -> Optional[BaseFixStrategy]:
        """
        Get strategy for error key.

        Args:
            error_key: Error key to look up

        Returns:
            Strategy instance or None if not found
        """
        return self.strategies.get(error_key)

    def has_strategy(self, error_key: str) -> bool:
        """
        Check if strategy exists for error key.

        Args:
            error_key: Error key to check

        Returns:
            True if strategy exists
        """
        return error_key in self.strategies

    def list_strategies(self) -> List[str]:
        """
        List all registered error keys.

        Returns:
            List of error keys with registered strategies
        """
        return list(self.strategies.keys())

    def initialize_strategies(self) -> None:
        """
        Initialize and register all LOW severity strategies.

        This method imports and registers all 7 LOW severity
        fix strategy implementations.
        """
        if self._initialized:
            logger.debug("Strategies already initialized")
            return

        logger.info("Initializing fix strategies...")

        try:
            # Import DEMO strategy (for testing)
            from .demo_log_viewer import DemoLogViewerStrategy

            # Import AI REPAIR strategies (Phase 2 - Fortex TOOL KIT automation)
            from .ai_repair import (
                MissingIntermediateFixStrategy,
                NoPowerUpAIRepairStrategy,
                NoShutdownAIRepairStrategy,
                TwoIdenticalStatusesFixStrategy,
                DrivingOriginFixStrategy,
            )

            # Import legacy LOW severity strategies (kept for reference)
            from .excessive_log_in import ExcessiveLogInFixStrategy
            from .excessive_log_out import ExcessiveLogOutFixStrategy

            # Register strategies
            strategies = [
                DemoLogViewerStrategy(),  # Demo strategy first

                # AI REPAIR strategies (use Fortex TOOL KIT button)
                MissingIntermediateFixStrategy(),
                NoPowerUpAIRepairStrategy(),
                NoShutdownAIRepairStrategy(),
                TwoIdenticalStatusesFixStrategy(),
                DrivingOriginFixStrategy(),

                # Custom strategies (require PTHORA AI logic)
                ExcessiveLogInFixStrategy(),
                ExcessiveLogOutFixStrategy(),
            ]

            for strategy in strategies:
                self.register(strategy)

            self._initialized = True
            logger.info(f"Initialized {len(strategies)} fix strategies")

        except ImportError as e:
            logger.error(f"Failed to import strategies: {e}")
            logger.warning("Some strategies may not be implemented yet")


# Global registry instance
strategy_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    """Get global strategy registry instance."""
    return strategy_registry

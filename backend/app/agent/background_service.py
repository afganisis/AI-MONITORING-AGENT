"""
Background service for AI Agent polling and fix execution.
"""

import asyncio
from typing import Optional, List
from datetime import datetime
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db_session
from ..database.models import Error, Fix, AgentConfig
from ..fortex.client import FortexAPIClient
from ..playwright.browser_manager import BrowserManager
from ..services.error_classifier import error_classifier
from ..websocket.manager import ws_manager
from ..config import settings
from .strategies.registry import strategy_registry


class AgentBackgroundService:
    """
    Main background service running asyncio event loop.

    Lifecycle:
    - Starts on application startup
    - Runs continuously while agent state = "running"
    - Graceful shutdown on SIGTERM/SIGINT

    Features:
    - Polls Fortex API for new errors
    - Classifies errors using error_classifier
    - Executes fix strategies via Playwright
    - Broadcasts WebSocket events
    - Respects agent configuration (polling interval, max concurrent fixes, etc.)
    """

    def __init__(self):
        # Fortex API client
        self.fortex_client: Optional[FortexAPIClient] = None

        # Playwright browser manager
        self.browser_manager: Optional[BrowserManager] = None

        # State management
        self.is_running = False
        self.current_task: Optional[asyncio.Task] = None

        # Concurrency control
        self.fix_semaphore: Optional[asyncio.Semaphore] = None

        # Company IDs to monitor (set via configuration)
        self.company_ids: List[str] = []

        # Selected driver IDs to monitor (set via API)
        self.selected_driver_ids: List[str] = []

    async def initialize(self):
        """Initialize Fortex API client and Playwright browser."""
        try:
            logger.info("Initializing Agent Background Service")

            # Initialize Fortex API client
            self.fortex_client = FortexAPIClient(
                base_url=settings.fortex_api_url,
                auth_token=settings.fortex_auth_token,
                system_name=settings.fortex_system_name
            )

            # Test Fortex API connection
            health_ok = await self.fortex_client.health_check()
            if not health_ok:
                logger.warning("Fortex API health check failed, but continuing...")

            # Initialize Playwright browser manager (skip in dry run mode only)
            # Note: Python 3.13+ event loop issues are handled in main.py via event loop policy
            skip_playwright = settings.agent_dry_run_mode

            if skip_playwright:
                logger.warning("Skipping Playwright initialization (dry run mode)")
                logger.warning("Agent will detect errors but NOT fix them automatically")
                self.browser_manager = None
            else:
                self.browser_manager = BrowserManager(
                    headless=settings.playwright_headless,
                    user_data_dir=settings.playwright_session_dir,
                    screenshot_dir=settings.playwright_screenshots_dir
                )

                await self.browser_manager.initialize()

                # Login to Fortex UI
                login_success = await self.browser_manager.login(
                    url=settings.fortex_ui_url,
                    username=settings.fortex_ui_username,
                    password=settings.fortex_ui_password
                )

                if not login_success:
                    raise Exception("Failed to login to Fortex UI")

                # Initialize fix strategies
                strategy_registry.initialize_strategies()

            logger.info("Agent Background Service initialized successfully")

        except Exception as e:
            logger.exception(f"Failed to initialize Agent Background Service: {e}")
            raise

    async def start(self):
        """Start background service."""
        if self.is_running:
            logger.warning("Agent is already running")
            return

        try:
            logger.info("Starting Agent Background Service")

            # Initialize if not already done
            if not self.fortex_client or not self.browser_manager:
                await self.initialize()

            self.is_running = True

            # Update agent state in database
            await self._update_agent_state("running")

            # Broadcast agent started
            await ws_manager.broadcast_agent_status({
                "state": "running",
                "message": "Agent started successfully"
            })

            # Start main loop
            self.current_task = asyncio.create_task(self._main_loop())

            logger.info("Agent Background Service started")

        except Exception as e:
            logger.exception(f"Failed to start Agent Background Service: {e}")
            self.is_running = False
            await self._update_agent_state("stopped")
            raise

    async def stop(self):
        """Stop background service gracefully."""
        if not self.is_running:
            logger.warning("Agent is not running")
            return

        logger.info("Stopping Agent Background Service")

        self.is_running = False

        # Cancel main loop task
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                logger.debug("Main loop task cancelled")

        # Update agent state
        await self._update_agent_state("stopped")

        # Broadcast agent stopped
        await ws_manager.broadcast_agent_status({
            "state": "stopped",
            "message": "Agent stopped"
        })

        logger.info("Agent Background Service stopped")

    async def pause(self):
        """Pause background service."""
        if not self.is_running:
            logger.warning("Agent is not running, cannot pause")
            return

        logger.info("Pausing Agent Background Service")
        await self._update_agent_state("paused")
        await ws_manager.broadcast_agent_status({
            "state": "paused",
            "message": "Agent paused"
        })

    async def resume(self):
        """Resume from paused state."""
        logger.info("Resuming Agent Background Service")
        await self._update_agent_state("running")
        await ws_manager.broadcast_agent_status({
            "state": "running",
            "message": "Agent resumed"
        })

    async def cleanup(self):
        """Cleanup resources."""
        try:
            logger.info("Cleaning up Agent Background Service")

            if self.browser_manager:
                await self.browser_manager.cleanup()

            if self.fortex_client:
                await self.fortex_client.close()

            logger.info("Agent Background Service cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def _main_loop(self):
        """Main agent loop."""
        logger.info("Agent main loop started")

        while self.is_running:
            try:
                # Load current configuration
                config = await self._load_config()

                # Check if paused
                if config.state == "paused":
                    await asyncio.sleep(10)
                    continue

                # Check if stopped
                if config.state == "stopped":
                    logger.info("Agent state is stopped, exiting main loop")
                    self.is_running = False
                    break

                # Initialize semaphore for concurrent fixes
                self.fix_semaphore = asyncio.Semaphore(config.max_concurrent_fixes)

                # 1. Poll Fortex API for errors
                await self._poll_errors(config)

                # 2. Process pending fixes
                await self._process_pending_fixes(config)

                # 3. Wait for next poll interval
                logger.debug(f"Waiting {config.polling_interval_seconds}s until next poll")
                await asyncio.sleep(config.polling_interval_seconds)

            except asyncio.CancelledError:
                logger.info("Main loop cancelled")
                break

            except Exception as e:
                logger.exception(f"Error in agent main loop: {e}")
                # Wait 1 minute on error before retrying
                await asyncio.sleep(60)

        logger.info("Agent main loop stopped")

    async def _poll_errors(self, config: AgentConfig):
        """Poll Fortex API and store new errors."""
        try:
            logger.info("Polling Fortex API for errors...")

            # Get company IDs to monitor
            company_ids = self.company_ids if self.company_ids else []

            if not company_ids:
                # If no specific companies configured, get all companies
                overview = await self.fortex_client.get_monitoring_overview()
                company_ids = [c.id for c in overview.companies if c.isError]
                logger.info(f"No specific companies configured, monitoring {len(company_ids)} companies with errors")

            # OPTIMIZATION: If specific drivers are selected, find which companies have those drivers FIRST
            # This uses Supabase to get company-driver mapping WITHOUT making API calls to Fortex
            if self.selected_driver_ids and len(self.selected_driver_ids) > 0:
                logger.info(f"🔍 Optimization: Finding companies for {len(self.selected_driver_ids)} selected drivers")
                company_ids = await self.fortex_client.get_companies_for_drivers_from_supabase(
                    self.selected_driver_ids
                )
                logger.info(f"✅ Optimization complete: Will query only {len(company_ids)} companies (NO unnecessary API calls)")

            # Fetch errors for each company (now optimized to only relevant companies)
            all_errors = await self.fortex_client.get_all_errors_from_companies(company_ids)

            # Filter by selected drivers (should already be filtered by company optimization, but kept as safety check)
            if self.selected_driver_ids:
                original_count = len(all_errors)
                all_errors = [e for e in all_errors if e.get("driver_id") in self.selected_driver_ids]
                if original_count != len(all_errors):
                    logger.info(f"Filtered {original_count} errors down to {len(all_errors)} errors for {len(self.selected_driver_ids)} selected drivers")

            logger.info(f"Found {len(all_errors)} total errors from {len(company_ids)} companies")

            # Store each error if new
            for error_data in all_errors:
                await self._store_error_if_new(error_data, config)

        except Exception as e:
            logger.exception(f"Failed to poll errors: {e}")

    async def _enrich_with_names(self, error_data: dict):
        """Enrich error data with driver and company names from Supabase."""
        try:
            from ..supabase.client import get_supabase_client

            supabase = get_supabase_client()
            companies = await supabase.get_companies_with_drivers()

            driver_id = error_data.get("driver_id")
            company_id = error_data.get("company_id")

            # Find company name
            for company in companies:
                if company.company_id == company_id:
                    error_data["company_name"] = company.company_name

                    # Find driver name
                    for driver in company.drivers:
                        if driver.driver_id == driver_id:
                            error_data["driver_name"] = driver.driver_name
                            break
                    break

        except Exception as e:
            logger.warning(f"Failed to enrich error data with names: {e}")

        return error_data

    async def _store_error_if_new(self, error_data: dict, config: AgentConfig):
        """Classify and store error if it doesn't already exist."""
        try:
            # Classify error
            error_message = error_data.get("error_message") or ""
            classification = error_classifier.classify(error_message)

            if not classification:
                logger.warning(f"❌ UNCLASSIFIED ERROR: '{error_message}'")
                return

            # Store all severity levels (LOW, MEDIUM, HIGH, CRITICAL)
            logger.debug(f"Processing {classification.severity.value} severity error: {classification.key}")

            # Enrich with driver and company names from Supabase
            error_data = await self._enrich_with_names(error_data)

            async with get_db_session() as db:
                # Check if error already exists
                stmt = select(Error).where(
                    Error.driver_id == error_data.get("driver_id"),
                    Error.error_key == classification.key,
                    Error.error_message == error_message,
                    Error.status.in_(["pending", "fixing"])
                )

                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    logger.debug(f"Error already exists: {classification.key} for driver {error_data.get('driver_id')}")
                    return

                # Create new error
                error = Error(
                    company_id=error_data.get("company_id"),
                    company_name=error_data.get("company_name"),
                    driver_id=error_data.get("driver_id"),
                    driver_name=error_data.get("driver_name"),
                    zeroeld_log_id=error_data.get("log_id"),
                    zeroeld_event_id=error_data.get("event_id"),
                    error_key=classification.key,
                    error_name=classification.name,
                    error_message=error_message,
                    severity=classification.severity.value,
                    category=classification.category.value,
                    status="pending",
                    error_metadata=error_data.get("metadata", {}),
                    discovered_at=datetime.utcnow()
                )

                db.add(error)
                await db.commit()
                await db.refresh(error)

                logger.info(
                    f"New error discovered: {classification.key} for "
                    f"driver {error_data.get('driver_name')} ({error.id})"
                )

                # Broadcast via WebSocket
                await ws_manager.broadcast_error_discovered({
                    "id": str(error.id),
                    "error_key": error.error_key,
                    "error_name": error.error_name,
                    "severity": error.severity,
                    "driver_name": error.driver_name,
                    "company_name": error.company_name
                })

        except Exception as e:
            logger.exception(f"Failed to store error: {e}")

    async def _process_pending_fixes(self, config: AgentConfig):
        """Process pending errors that need fixing."""
        try:
            async with get_db_session() as db:
                # Get pending errors (all severity levels, prioritize by severity)
                stmt = select(Error).where(
                    Error.status == "pending"
                ).order_by(Error.discovered_at.asc()).limit(10)

                result = await db.execute(stmt)
                pending_errors = result.scalars().all()

                if not pending_errors:
                    logger.debug("No pending errors to process")
                    return

                logger.info(f"Processing {len(pending_errors)} pending errors")

                # Process errors concurrently
                tasks = [
                    self._execute_fix_with_semaphore(error, config)
                    for error in pending_errors
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.exception(f"Failed to process pending fixes: {e}")

    async def _execute_fix_with_semaphore(self, error: Error, config: AgentConfig):
        """Execute fix with semaphore to limit concurrency."""
        async with self.fix_semaphore:
            await self._execute_fix(error, config)

    async def _execute_fix(self, error: Error, config: AgentConfig):
        """Execute fix for a single error."""
        try:
            logger.info(f"Executing fix for error {error.id} ({error.error_key})")

            # Get fix strategy
            strategy = strategy_registry.get_strategy(error.error_key)

            if not strategy:
                logger.warning(f"No strategy found for error key: {error.error_key}")
                return

            # Create Fix record
            fix = await self._create_fix_record(error, strategy.strategy_name)

            # Check if approval required
            if config.require_approval and not fix.approved_by:
                logger.info(f"Fix {fix.id} requires approval, skipping execution")
                await ws_manager.broadcast({
                    "type": "fix_approval_required",
                    "data": {
                        "fix_id": str(fix.id),
                        "error_id": str(error.id),
                        "strategy": strategy.strategy_name
                    }
                })
                return

            # Broadcast fix started
            await ws_manager.broadcast_fix_started({
                "fix_id": str(fix.id),
                "error_id": str(error.id),
                "strategy": strategy.strategy_name
            })

            # Update error status
            async with get_db_session() as db:
                error.status = "fixing"
                db.add(error)
                await db.commit()

            # Execute fix (with retry logic)
            if config.dry_run_mode:
                logger.info(f"Dry run mode: Simulating fix for {error.id}")
                from .strategies.base import FixResult
                result = FixResult(
                    success=True,
                    message=f"[DRY RUN] Would execute {strategy.strategy_name} for {error.error_key}",
                    execution_time_ms=0,
                )
            elif not self.browser_manager:
                logger.warning(f"Browser not initialized, cannot fix {error.id}")
                from .strategies.base import FixResult
                result = FixResult(
                    success=False,
                    message="Browser not initialized - cannot execute Playwright fix",
                    execution_time_ms=0,
                )
            else:
                result = await strategy.retry(error, fix, self.browser_manager, max_retries=3)

            # Update fix result
            await self._update_fix_result(fix, result)

            # Update error status
            async with get_db_session() as db:
                stmt = select(Error).where(Error.id == error.id)
                result_db = await db.execute(stmt)
                error_db = result_db.scalar_one()

                if result.success:
                    error_db.status = "fixed"
                    error_db.fixed_at = datetime.utcnow()

                    await ws_manager.broadcast_fix_success({
                        "fix_id": str(fix.id),
                        "error_id": str(error.id),
                        "message": result.message
                    })
                else:
                    error_db.status = "failed"

                    await ws_manager.broadcast_fix_failed({
                        "fix_id": str(fix.id),
                        "error_id": str(error.id),
                        "message": result.message
                    })

                await db.commit()

            logger.info(f"Fix execution complete for error {error.id}: {result.success}")

        except Exception as e:
            logger.exception(f"Failed to execute fix for error {error.id}: {e}")

            # Mark as failed
            async with get_db_session() as db:
                stmt = select(Error).where(Error.id == error.id)
                result_db = await db.execute(stmt)
                error_db = result_db.scalar_one_or_none()

                if error_db:
                    error_db.status = "failed"
                    await db.commit()

    async def _create_fix_record(self, error: Error, strategy_name: str) -> Fix:
        """Create Fix record in database."""
        async with get_db_session() as db:
            fix = Fix(
                error_id=error.id,
                strategy_name=strategy_name,
                status="pending",
                started_at=datetime.utcnow()
            )

            db.add(fix)
            await db.commit()
            await db.refresh(fix)

            return fix

    async def _update_fix_result(self, fix: Fix, result):
        """Update Fix record with execution result."""
        async with get_db_session() as db:
            stmt = select(Fix).where(Fix.id == fix.id)
            result_db = await db.execute(stmt)
            fix_db = result_db.scalar_one()

            fix_db.status = "success" if result.success else "failed"
            fix_db.completed_at = datetime.utcnow()
            fix_db.result_message = result.message
            fix_db.execution_time_ms = result.execution_time_ms
            fix_db.screenshot_path = result.screenshot_path

            await db.commit()

    async def _load_config(self) -> AgentConfig:
        """Load agent configuration from database."""
        async with get_db_session() as db:
            stmt = select(AgentConfig).limit(1)
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()

            if not config:
                # Create default config
                config = AgentConfig(
                    state="stopped",
                    polling_interval_seconds=settings.agent_polling_interval_seconds,
                    max_concurrent_fixes=settings.agent_max_concurrent_fixes,
                    require_approval=settings.agent_require_approval,
                    dry_run_mode=settings.agent_dry_run_mode
                )
                db.add(config)
                await db.commit()
                await db.refresh(config)

            return config

    async def _update_agent_state(self, state: str):
        """Update agent state in database."""
        async with get_db_session() as db:
            stmt = select(AgentConfig).limit(1)
            result = await db.execute(stmt)
            config = result.scalar_one_or_none()

            if config:
                config.state = state
                config.last_run_at = datetime.utcnow()
                await db.commit()

    def set_company_ids(self, company_ids: List[str]):
        """
        Set specific company IDs to monitor.

        Args:
            company_ids: List of company UUIDs
        """
        self.company_ids = company_ids
        logger.info(f"Agent will monitor {len(company_ids)} specific companies")

    def set_selected_driver_ids(self, driver_ids: List[str]):
        """
        Set specific driver IDs to monitor and fix.

        Args:
            driver_ids: List of driver UUIDs
        """
        self.selected_driver_ids = driver_ids
        logger.info(f"Agent will monitor {len(driver_ids)} selected drivers")

    def get_selected_driver_ids(self) -> List[str]:
        """
        Get currently selected driver IDs.

        Returns:
            List of driver UUIDs
        """
        return self.selected_driver_ids


# Global agent service instance
agent_service = AgentBackgroundService()


def get_agent_service() -> AgentBackgroundService:
    """Get global agent service instance."""
    return agent_service

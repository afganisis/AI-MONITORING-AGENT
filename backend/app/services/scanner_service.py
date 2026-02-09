"""Scanner service for running Smart Analyze on drivers."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
import uuid

from app.playwright.browser_manager import BrowserManager
from app.fortex.client import FortexAPIClient
from app.config import get_settings
from app.database.session import get_db_session
from app.database.models import Error
from app.services.progress_tracker import progress_tracker
from app.services.error_classifier import error_classifier

settings = get_settings()


class ScannerService:
    """Service for scanning driver logs and detecting errors."""

    def __init__(self):
        """Initialize scanner service."""
        self.browser_manager = None
        self.fortex_client = None

    async def scan_drivers(
        self,
        driver_ids: List[str],
        company_id: str | None = None,
        scan_id: str | None = None,
        company_data: Any = None,
        driver_names_map: Dict[str, str] = None,
        company_name: str = None
    ) -> Dict[str, Any]:
        """
        Scan multiple drivers in parallel.

        Args:
            driver_ids: List of driver UUIDs to scan
            company_id: Optional company ID
            scan_id: Optional scan ID for progress tracking
            company_data: Pre-fetched company smart analyze data
            driver_names_map: Map of driver_id -> driver_name from Supabase
            company_name: Company name from Supabase

        Returns:
            Scan results with statistics
        """
        logger.info(f"Starting scan for {len(driver_ids)} drivers...")

        # Initialize API client (NO Playwright needed for scanning!)
        self.fortex_client = FortexAPIClient(
            base_url=settings.fortex_api_url,
            auth_token=settings.fortex_auth_token
        )

        try:

            # Scan drivers sequentially with progress updates
            all_results = []

            for i, driver_id in enumerate(driver_ids):
                logger.info(f"Scanning driver {i + 1}/{len(driver_ids)}: {driver_id[:8]}...")

                # Update progress
                if scan_id:
                    progress_tracker.update_driver(scan_id, i, driver_id)

                # Scan single driver with enriched names
                result = await self._scan_single_driver(
                    driver_id,
                    company_id,
                    company_data,
                    driver_names_map=driver_names_map,
                    company_name_override=company_name
                )
                all_results.append(result)

            # Calculate statistics
            successful_scans = sum(1 for r in all_results if isinstance(r, dict) and r.get('success'))
            total_errors = sum(r.get('error_count', 0) for r in all_results if isinstance(r, dict))

            return {
                'success': True,
                'total_drivers': len(driver_ids),
                'successful_scans': successful_scans,
                'failed_scans': len(driver_ids) - successful_scans,
                'total_errors_found': total_errors,
                'results': all_results
            }

        except Exception as e:
            logger.exception(f"Scan failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            # Cleanup
            if self.fortex_client:
                await self.fortex_client.close()


    async def _scan_single_driver(
        self,
        driver_id: str,
        company_id: str | None,
        company_data: Any = None,
        driver_names_map: Dict[str, str] = None,
        company_name_override: str = None
    ) -> Dict[str, Any]:
        """
        Scan a single driver.

        Args:
            driver_id: Driver UUID
            company_id: Optional company ID
            company_data: Pre-fetched company smart analyze data
            driver_names_map: Map of driver_id -> driver_name from Supabase
            company_name_override: Company name from Supabase (overrides company_data)

        Returns:
            Scan result
        """
        try:
            logger.info(f"Scanning driver {driver_id[:8]}...")

            # Extract errors for this specific driver from company data
            errors = []

            # Get driver name from Supabase map FIRST (priority), then fallback
            driver_name = None
            if driver_names_map and driver_id in driver_names_map:
                driver_name = driver_names_map[driver_id]
                logger.info(f"Using driver name from Supabase: {driver_name}")

            if not driver_name:
                driver_name = f"driver_{driver_id[:8]}"

            # Get company name from override (Supabase) FIRST, then company_data
            company_name = company_name_override
            if not company_name and company_data and hasattr(company_data, 'company_name'):
                company_name = company_data.company_name

            if company_data and hasattr(company_data, 'drivers'):
                # Find this driver's data
                for driver_log in company_data.drivers:
                    if (driver_log.driver_id == driver_id or driver_log.driverId == driver_id):
                        # Get driver name from API or use fallback
                        if hasattr(driver_log, 'driver_name') and driver_log.driver_name:
                            driver_name = driver_log.driver_name
                        elif hasattr(driver_log.driverState, 'account_id'):
                            # Try to extract from driverState if available
                            driver_name = driver_log.driverState.account_id or driver_name

                        # Extract errors from driver's logCheckErrors
                        if hasattr(driver_log, 'logCheckErrors') and driver_log.logCheckErrors:
                            for error in driver_log.logCheckErrors:
                                # Get error type and message
                                error_type = getattr(error, 'errorType', None) or getattr(error, 'type', None) or 'unknown'
                                error_message = getattr(error, 'errorMessage', None) or getattr(error, 'message', None) or 'Unknown Error'

                                errors.append({
                                    'type': error_type,
                                    'name': error_message,
                                    'message': error_message,
                                    'severity': 'medium',  # Default severity - will classify later
                                    'category': getattr(error, 'eventCode', None) or error_type or 'uncategorized',
                                    'date': getattr(error, 'errorTime', None) or getattr(error, 'timestamp', None)
                                })
                        break

            logger.info(f"Driver {driver_id[:8]} ({driver_name}): {len(errors)} errors found")

            # Save errors to database
            if errors:
                await self._save_errors_to_db(
                    errors=errors,
                    driver_id=driver_id,
                    driver_name=driver_name,
                    company_id=company_id or "unknown",
                    company_name=company_name
                )

            return {
                'success': True,
                'driver_id': driver_id,
                'driver_name': driver_name,
                'error_count': len(errors),
                'errors': errors
            }

        except Exception as e:
            logger.exception(f"Failed to scan driver {driver_id[:8]}: {e}")
            return {
                'success': False,
                'driver_id': driver_id,
                'error': str(e)
            }

    async def _save_errors_to_db(
        self,
        errors: List[Dict[str, Any]],
        driver_id: str,
        driver_name: str,
        company_id: str,
        company_name: str = None
    ):
        """Save errors to database with proper classification."""
        try:
            async with get_db_session() as session:
                saved_count = 0
                skipped_count = 0

                for error in errors:
                    error_message = error.get('message', '') or error.get('name', '')

                    # Use error_classifier for proper classification
                    classification = error_classifier.classify(error_message)

                    if classification:
                        # Use classified values
                        error_key = classification.key
                        error_name = classification.name
                        severity = classification.severity.value
                        category = classification.category.value
                    else:
                        # Fallback for unclassified errors
                        error_key = error.get('type', 'unknown')
                        error_name = error.get('name', 'Unknown Error')
                        severity = error.get('severity', 'medium')
                        category = error.get('category', 'uncategorized')
                        logger.debug(f"Unclassified error: '{error_message[:50]}...'")

                    db_error = Error(
                        driver_id=driver_id,
                        driver_name=driver_name,
                        company_id=company_id,
                        company_name=company_name,
                        error_key=error_key,
                        error_name=error_name,
                        error_message=error_message,
                        severity=severity,
                        category=category,
                        status='pending',
                        error_metadata=error
                    )
                    session.add(db_error)
                    saved_count += 1

                await session.commit()
                logger.info(f"Saved {saved_count} errors to database: driver={driver_id[:8]}, company={company_id}, driver_name={driver_name}, company_name={company_name}")
                if skipped_count > 0:
                    logger.warning(f"Skipped {skipped_count} unclassified errors")

        except Exception as e:
            logger.exception(f"Failed to save errors to database: {e}")


# Global instance
scanner_service = ScannerService()

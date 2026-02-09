"""
Fortex API HTTP client with authentication and error handling.
"""

import httpx
import asyncio
from typing import List, Optional, Dict, Any
from loguru import logger

from .models import (
    MonitoringOverview,
    SmartAnalyzeResponse,
    CompanySummary,
    DriverLog,
    LogCheckError
)


class FortexAPIClient:
    """
    Async HTTP client for Fortex API.

    Features:
    - Hardcoded authorization header
    - Redis-aware (10min cache on server side)
    - Async HTTP operations using httpx
    - Automatic retry on network errors
    - Response validation using Pydantic models
    """

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        system_name: str = "zero",
        timeout: int = 30
    ):
        """
        Initialize Fortex API client.

        Args:
            base_url: Fortex API base URL
            auth_token: Authorization token (y3He9C57ecfmMAsR19)
            system_name: System name for x-system-name header (default: "zero")
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.system_name = system_name
        self.timeout = timeout

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": self.auth_token,
                "x-system-name": self.system_name,
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(timeout)
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/monitoring")
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors after retries
            httpx.TimeoutException: On timeout after retries
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{max_retries})")

                response = await self.client.request(method, url, **kwargs)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s before retry")
                    await asyncio.sleep(retry_after)
                    continue

                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()

                # Return JSON response
                return response.json()

            except httpx.TimeoutException as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff

            except httpx.HTTPStatusError as e:
                # Don't retry client errors (4xx) except 429
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    logger.error(f"Client error {e.response.status_code}: {e}")
                    raise

                # Retry server errors (5xx)
                if e.response.status_code >= 500:
                    logger.error(f"Server error {e.response.status_code}, retrying...")
                    await asyncio.sleep(10)
                    continue

                raise

            except Exception as e:
                logger.exception(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(5 * (attempt + 1))

        raise Exception(f"Failed after {max_retries} attempts")

    async def get_monitoring_overview(self) -> MonitoringOverview:
        """
        Get monitoring overview for all companies.

        Endpoint: GET /monitoring
        Cached: 600 seconds (10 minutes) on server

        Returns:
            MonitoringOverview with company summaries and total statistics
        """
        try:
            logger.info("Fetching monitoring overview from Fortex API")
            data = await self._make_request("GET", "/monitoring")

            overview = MonitoringOverview(**data)
            logger.info(
                f"Retrieved {len(overview.companies)} companies, "
                f"total errors: {overview.totalNumberOfError}"
            )

            return overview

        except Exception as e:
            logger.exception(f"Failed to get monitoring overview: {e}")
            raise

    async def get_smart_analyze(self, company_id: str) -> SmartAnalyzeResponse:
        """
        Get detailed analysis for a specific company.

        Endpoint: GET /monitoring/smart-analyze/:companyId
        Cached: 600 seconds (10 minutes) on server

        Args:
            company_id: UUID of the company to analyze

        Returns:
            SmartAnalyzeResponse with driver logs and logCheckErrors
        """
        try:
            logger.info(f"Fetching smart analyze for company {company_id}")
            data = await self._make_request("GET", f"/monitoring/smart-analyze/{company_id}")

            # Handle different response formats
            if isinstance(data, list):
                # Response is array of driver logs
                drivers = [DriverLog(**log) for log in data]
                total_errors = sum(len(d.logCheckErrors) for d in drivers)

                response = SmartAnalyzeResponse(
                    drivers=drivers,
                    company_id=company_id,
                    total_errors=total_errors
                )
            elif isinstance(data, dict):
                # Response is object with drivers array
                response = SmartAnalyzeResponse(
                    company_id=company_id,
                    **data
                )
            else:
                raise ValueError(f"Unexpected response format: {type(data)}")

            logger.info(
                f"Retrieved {len(response.drivers)} drivers for company {company_id}, "
                f"total errors: {response.total_errors}"
            )

            return response

        except Exception as e:
            logger.exception(f"Failed to get smart analyze for company {company_id}: {e}")
            raise

    async def get_smart_analyze_for_companies(
        self,
        company_ids: List[str]
    ) -> Dict[str, SmartAnalyzeResponse]:
        """
        Get smart analyze for multiple companies.

        Args:
            company_ids: List of company UUIDs to analyze

        Returns:
            Dictionary mapping company_id to SmartAnalyzeResponse
        """
        logger.info(f"Fetching smart analyze for {len(company_ids)} companies")

        results = {}
        for company_id in company_ids:
            try:
                response = await self.get_smart_analyze(company_id)
                results[company_id] = response
            except Exception as e:
                logger.error(f"Failed to fetch company {company_id}: {e}")
                continue

        logger.info(f"Successfully fetched {len(results)}/{len(company_ids)} companies")
        return results

    async def get_companies_for_drivers_from_supabase(
        self,
        driver_ids: List[str]
    ) -> List[str]:
        """
        Determine which companies contain the specified drivers using Supabase.

        This uses the existing Supabase client to get company-driver mapping
        WITHOUT making unnecessary API calls to Fortex.

        Args:
            driver_ids: List of driver IDs to find

        Returns:
            List of company IDs that contain at least one of the specified drivers
        """
        from ..supabase.client import get_supabase_client

        logger.info(f"🔍 Finding companies for {len(driver_ids)} selected drivers using Supabase (NO Fortex API calls)")

        try:
            supabase = get_supabase_client()
            companies = await supabase.get_companies_with_drivers()

            # Build driver_id to company_id mapping
            companies_with_drivers = set()

            for company in companies:
                company_driver_ids = {driver.driver_id for driver in company.drivers}

                # Check if any selected driver belongs to this company
                if any(driver_id in company_driver_ids for driver_id in driver_ids):
                    companies_with_drivers.add(company.company_id)
                    logger.info(f"✓ Company {company.company_name} contains selected driver(s)")

            result = list(companies_with_drivers)
            logger.info(f"✅ Found {len(result)} companies (optimized - NO unnecessary Fortex API calls)")
            return result

        except Exception as e:
            logger.error(f"Failed to get companies from Supabase: {e}")
            # Fallback: return empty list to avoid querying all companies
            return []

    async def get_all_errors_from_companies(
        self,
        company_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get all logCheckErrors from specified companies.

        Args:
            company_ids: List of company UUIDs to scan

        Returns:
            List of error dictionaries with company and driver context
        """
        all_errors = []

        responses = await self.get_smart_analyze_for_companies(company_ids)

        for company_id, response in responses.items():
            logger.debug(f"Processing company {company_id}, {len(response.drivers)} drivers")

            for driver_log in response.drivers:
                # Check if logCheckErrors exist at driver level
                driver_level_errors = len(driver_log.logCheckErrors)
                logger.debug(f"Driver {driver_log.driver_id}: {driver_level_errors} errors at driver level")

                # Process driver-level logCheckErrors
                for idx, error in enumerate(driver_log.logCheckErrors):
                    error_dict = {
                        "company_id": company_id,
                        "company_name": response.company_name,
                        "driver_id": driver_log.driver_id or driver_log.driverId,
                        "driver_name": driver_log.driver_name,
                        "log_id": error.id,  # Use 'id' field from API
                        "event_id": error.id,  # Same as log_id
                        "error_message": error.errorMessage,  # Use camelCase field
                        "error_type": error.errorType,  # Use camelCase field
                        "timestamp": str(error.errorTime) if error.errorTime else None,
                        "metadata": {
                            "eventCode": error.eventCode,
                            "errorTime": error.errorTime
                        }
                    }
                    all_errors.append(error_dict)

                # Also check if errors are nested inside driverLogs array
                if driver_log.driverLogs:
                    logger.debug(f"Driver has {len(driver_log.driverLogs)} log entries")
                    for log_entry in driver_log.driverLogs:
                        # Check if this log entry has logCheckErrors
                        if isinstance(log_entry, dict) and 'logCheckErrors' in log_entry:
                            log_errors = log_entry.get('logCheckErrors', [])
                            logger.debug(f"Found {len(log_errors)} errors in log entry")

                            for error_item in log_errors:
                                # Extract error message from various possible fields
                                error_message = (
                                    error_item.get('error_message') or
                                    error_item.get('message') or
                                    error_item.get('errorMessage') or
                                    str(error_item)
                                )

                                error_dict = {
                                    "company_id": company_id,
                                    "company_name": response.company_name,
                                    "driver_id": driver_log.driver_id or driver_log.driverId,
                                    "driver_name": driver_log.driver_name,
                                    "log_id": error_item.get('log_id') or error_item.get('logId'),
                                    "event_id": error_item.get('event_id') or error_item.get('eventId'),
                                    "error_message": error_message,
                                    "error_type": error_item.get('type'),
                                    "timestamp": error_item.get('timestamp') or error_item.get('date'),
                                    "metadata": error_item.get('metadata', {})
                                }
                                all_errors.append(error_dict)

        logger.info(f"Collected {len(all_errors)} errors from {len(company_ids)} companies")
        return all_errors

    async def smart_analyze_driver(
        self,
        driver_id: str,
        date_from: str,
        date_to: str
    ) -> Dict[str, Any]:
        """
        Run AI-powered Smart Analyze for a specific driver and date range.

        Endpoint: POST /monitoring/smart-analyze

        Args:
            driver_id: UUID of the driver
            date_from: Start date in format "YYYY-MM-DD"
            date_to: End date in format "YYYY-MM-DD"

        Returns:
            Dict with analysis results containing:
            - errors: List of detected errors with types and severity
            - summary: Overall compliance status
            - recommendations: Suggested fixes

        Example:
            >>> result = await client.smart_analyze_driver(
            ...     driver_id="9bd39206-6ec6-4603-8037-7b85c6bf3321",
            ...     date_from="2026-01-21",
            ...     date_to="2026-01-29"
            ... )
        """
        try:
            logger.info(
                f"Running Smart Analyze for driver {driver_id[:8]}... "
                f"from {date_from} to {date_to}"
            )

            payload = {
                "driverId": driver_id,
                "dateFrom": date_from,
                "dateTo": date_to
            }

            data = await self._make_request(
                "POST",
                "/monitoring/smart-analyze",
                json=payload
            )

            logger.info(f"Smart Analyze complete for driver {driver_id[:8]}...")
            return data

        except Exception as e:
            logger.exception(f"Failed to run Smart Analyze for driver {driver_id}: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if Fortex API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            await self.get_monitoring_overview()
            logger.info("Fortex API health check: OK")
            return True
        except Exception as e:
            logger.error(f"Fortex API health check failed: {e}")
            return False

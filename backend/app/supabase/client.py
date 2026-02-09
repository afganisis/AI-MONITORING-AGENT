"""
Supabase Edge Function client for getting company/driver allocations.
"""

import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from pydantic import BaseModel


class Driver(BaseModel):
    """Driver information from Supabase."""
    driver_id: str
    driver_name: str
    # Add more fields as needed from edge function response


class Company(BaseModel):
    """Company information from Supabase."""
    company_id: str
    company_name: str
    drivers: List[Driver] = []
    # Add more fields as needed


class SupabaseClient:
    """
    Client for Supabase edge functions.

    Fetches company and driver allocations from:
    https://mtfkrydqvyjxjvnaqtjj.supabase.co/functions/v1/get-daily-allocations
    """

    def __init__(self, edge_function_url: str):
        """
        Initialize Supabase client.

        Args:
            edge_function_url: Full URL to edge function
        """
        self.edge_function_url = edge_function_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def get_daily_allocations(self) -> List[Dict[str, Any]]:
        """
        Fetch daily allocations from Supabase edge function.

        Returns:
            List of allocation dictionaries with company/driver info

        Raises:
            httpx.HTTPError: If HTTP request fails
            Exception: If response parsing fails
        """
        try:
            logger.debug(f"Fetching daily allocations from {self.edge_function_url}")

            response = await self.client.get(self.edge_function_url)
            response.raise_for_status()

            response_data = response.json()

            # Handle different response formats
            # If response is {"data": [...]} extract the array
            if isinstance(response_data, dict) and "data" in response_data:
                data = response_data["data"]
            elif isinstance(response_data, list):
                data = response_data
            else:
                logger.warning(f"Unexpected response format: {type(response_data)}. Got: {str(response_data)[:200]}")
                data = []

            if not isinstance(data, list):
                logger.warning(f"Response data is not a list, converting to empty list")
                data = []

            logger.info(f"Retrieved {len(data)} allocations from Supabase edge function")
            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching allocations: {e}")
            raise
        except Exception as e:
            logger.exception(f"Failed to parse allocations response: {e}")
            raise

    async def get_companies_with_drivers(self) -> List[Company]:
        """
        Get structured list of companies with their drivers.

        Returns:
            List of Company objects with nested drivers

        Raises:
            Exception: If allocation fetch or parsing fails
        """
        try:
            logger.debug("Getting companies with drivers")
            allocations = await self.get_daily_allocations()

            if not allocations:
                logger.warning("No allocations returned from Supabase edge function")
                return []

            # Group by company
            companies_dict: Dict[str, Company] = {}
            skipped_count = 0

            for allocation in allocations:
                # Try different field name variations
                company_id = (
                    allocation.get("company_id") or
                    allocation.get("companyId") or
                    allocation.get("company_eld_id")
                )
                company_name = allocation.get("company_name") or allocation.get("companyName")

                driver_id = (
                    allocation.get("driver_id") or
                    allocation.get("driverId") or
                    allocation.get("driver_eld_id")
                )
                driver_name = allocation.get("driver_name") or allocation.get("driverName")

                if not company_id:
                    skipped_count += 1
                    continue

                # Create company if not exists
                if company_id not in companies_dict:
                    companies_dict[company_id] = Company(
                        company_id=company_id,
                        company_name=company_name or f"Company {company_id[:8]}",
                        drivers=[]
                    )

                # Add driver if exists
                if driver_id:
                    # Check if driver already added
                    existing_driver_ids = {d.driver_id for d in companies_dict[company_id].drivers}

                    if driver_id not in existing_driver_ids:
                        companies_dict[company_id].drivers.append(
                            Driver(
                                driver_id=driver_id,
                                driver_name=driver_name or f"Driver {driver_id[:8]}"
                            )
                        )

            companies = list(companies_dict.values())

            # Sort companies by name
            companies.sort(key=lambda c: c.company_name)

            total_drivers = sum(len(c.drivers) for c in companies)
            logger.info(
                f"Structured {len(companies)} companies with {total_drivers} total drivers "
                f"(skipped {skipped_count} allocations with missing company_id)"
            )
            return companies

        except Exception as e:
            logger.exception(f"Failed to structure companies with drivers: {e}")
            raise

    async def get_all_company_ids(self) -> List[str]:
        """
        Get list of all company IDs.

        Returns:
            List of company UUID strings
        """
        companies = await self.get_companies_with_drivers()
        return [c.company_id for c in companies]

    async def get_all_driver_ids(self) -> List[str]:
        """
        Get list of all driver IDs across all companies.

        Returns:
            List of driver UUID strings
        """
        companies = await self.get_companies_with_drivers()
        all_drivers = []

        for company in companies:
            all_drivers.extend([d.driver_id for d in company.drivers])

        return all_drivers


# Global Supabase client instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Get global Supabase client instance.

    Returns:
        SupabaseClient instance
    """
    global _supabase_client

    if _supabase_client is None:
        # Default edge function URL (filtered version - only ZEROELD, active, non-test companies)
        edge_function_url = "https://mtfkrydqvyjxjvnaqtjj.supabase.co/functions/v1/get-filtered-allocations"
        _supabase_client = SupabaseClient(edge_function_url)

    return _supabase_client

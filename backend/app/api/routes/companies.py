"""
Companies and drivers API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from loguru import logger

from ...supabase.client import get_supabase_client, Company, Driver
from ...agent.background_service import agent_service


router = APIRouter()


class DriverSelectionRequest(BaseModel):
    """Request to set selected drivers for monitoring."""
    driver_ids: List[str]


class DriverSelectionResponse(BaseModel):
    """Response after setting driver selection."""
    success: bool
    message: str
    selected_count: int
    driver_ids: List[str]


@router.get("/companies", response_model=List[Company])
async def get_companies():
    """
    Get all companies with their drivers from Supabase.

    Returns:
        List of companies with nested driver information
    """
    try:
        logger.info("GET /api/companies - Fetching companies from Supabase")
        supabase = get_supabase_client()

        companies = await supabase.get_companies_with_drivers()
        logger.info(f"GET /api/companies - Retrieved {len(companies)} companies with {sum(len(c.drivers) for c in companies)} drivers")

        return companies

    except Exception as e:
        logger.exception(f"GET /api/companies - Failed to fetch companies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch companies: {str(e)}"
        )


@router.get("/companies-health", response_model=dict)
async def companies_health():
    """
    Health check endpoint for companies service.

    Tests connectivity to Supabase edge function.

    Returns:
        Health status with response time
    """
    import time
    try:
        start_time = time.time()
        logger.debug("Health check: Testing Supabase connectivity")
        supabase = get_supabase_client()
        companies = await supabase.get_companies_with_drivers()
        elapsed = time.time() - start_time

        total_drivers = sum(len(c.drivers) for c in companies)
        logger.info(f"Health check: OK - {len(companies)} companies, {total_drivers} drivers in {elapsed:.2f}s")

        return {
            "status": "healthy",
            "companies_count": len(companies),
            "drivers_count": total_drivers,
            "response_time_seconds": round(elapsed, 2)
        }

    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Companies service unhealthy: {str(e)}"
        )


@router.get("/companies/{company_id}/drivers", response_model=List[Driver])
async def get_company_drivers(company_id: str):
    """
    Get drivers for a specific company.

    Args:
        company_id: UUID of the company

    Returns:
        List of drivers for the company
    """
    try:
        logger.info(f"Fetching drivers for company {company_id}")
        supabase = get_supabase_client()
        companies = await supabase.get_companies_with_drivers()

        # Find the company
        company = next((c for c in companies if c.company_id == company_id), None)

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company {company_id} not found"
            )

        logger.info(f"Returning {len(company.drivers)} drivers for company {company.company_name}")
        return company.drivers

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch drivers for company {company_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch drivers: {str(e)}"
        )


@router.post("/drivers/select", response_model=DriverSelectionResponse)
async def select_drivers(request: DriverSelectionRequest):
    """
    Set which drivers the AI Agent should monitor and fix.

    Args:
        request: List of driver IDs to monitor

    Returns:
        Success response with selected driver count
    """
    try:
        driver_ids = request.driver_ids

        logger.info(f"Setting {len(driver_ids)} drivers for AI Agent monitoring")

        # Store selected driver IDs in agent service
        agent_service.set_selected_driver_ids(driver_ids)

        return DriverSelectionResponse(
            success=True,
            message=f"Successfully selected {len(driver_ids)} drivers for monitoring",
            selected_count=len(driver_ids),
            driver_ids=driver_ids
        )

    except Exception as e:
        logger.exception(f"Failed to set driver selection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set driver selection: {str(e)}"
        )


@router.get("/drivers/selected", response_model=List[str])
async def get_selected_drivers():
    """
    Get currently selected driver IDs.

    Returns:
        List of selected driver IDs
    """
    try:
        # Get from agent service
        selected_ids = agent_service.get_selected_driver_ids()

        logger.info(f"Returning {len(selected_ids)} selected drivers")
        return selected_ids

    except Exception as e:
        logger.exception(f"Failed to get selected drivers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get selected drivers: {str(e)}"
        )

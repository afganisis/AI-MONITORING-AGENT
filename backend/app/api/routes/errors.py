"""Error management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from loguru import logger

from app.database.session import get_db
from app.database.models import Error

router = APIRouter()


class ErrorResponse(BaseModel):
    """Error response model."""

    id: str
    zeroeld_log_id: Optional[str] = None
    zeroeld_event_id: Optional[str] = None
    driver_id: str
    driver_name: Optional[str] = None
    company_id: str
    company_name: Optional[str] = None
    error_key: str
    error_name: str
    error_message: Optional[str] = None
    severity: str
    status: str
    error_metadata: Optional[dict] = None
    discovered_at: datetime
    fixed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Convert ORM object to response model."""
        return cls(
            id=str(obj.id),
            zeroeld_log_id=obj.zeroeld_log_id,
            zeroeld_event_id=obj.zeroeld_event_id,
            driver_id=obj.driver_id,
            driver_name=obj.driver_name,
            company_id=obj.company_id,
            company_name=obj.company_name,
            error_key=obj.error_key,
            error_name=obj.error_name,
            error_message=obj.error_message,
            severity=obj.severity,
            status=obj.status,
            error_metadata=obj.error_metadata,
            discovered_at=obj.discovered_at,
            fixed_at=obj.fixed_at,
            created_at=obj.created_at,
        )


class ErrorListResponse(BaseModel):
    """Paginated error list response."""

    errors: List[ErrorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorStatsResponse(BaseModel):
    """Error statistics response."""

    total_errors: int
    by_status: dict
    by_severity: dict
    by_error_key: dict


@router.get("/", response_model=ErrorListResponse)
async def list_errors(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    error_key: Optional[str] = None,
    driver_id: Optional[str] = None,
    company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of errors with optional filters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by status (pending, fixing, fixed, failed, ignored)
        severity: Filter by severity (low, medium, high, critical)
        error_key: Filter by error key
        driver_id: Filter by driver ID
        company_id: Filter by company ID

    Returns:
        Paginated list of errors
    """
    # Build filters
    filters = []
    if status:
        filters.append(Error.status == status)
    if severity:
        filters.append(Error.severity == severity)
    if error_key:
        filters.append(Error.error_key == error_key)
    if driver_id:
        filters.append(Error.driver_id == driver_id)
    if company_id:
        filters.append(Error.company_id == company_id)

    # Get total count
    count_query = select(func.count(Error.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated errors
    offset = (page - 1) * page_size
    query = (
        select(Error)
        .order_by(Error.discovered_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    errors = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return ErrorListResponse(
        errors=[ErrorResponse.from_orm(error) for error in errors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=ErrorStatsResponse)
async def get_error_stats(db: AsyncSession = Depends(get_db)):
    """
    Get error statistics.

    Returns:
        Aggregated statistics about errors (optimized with SQL aggregation)
    """
    # Get total count efficiently
    total_result = await db.execute(select(func.count(Error.id)))
    total_errors = total_result.scalar_one()

    # Count by status using SQL GROUP BY
    status_result = await db.execute(
        select(Error.status, func.count(Error.id))
        .group_by(Error.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Count by severity using SQL GROUP BY
    severity_result = await db.execute(
        select(Error.severity, func.count(Error.id))
        .group_by(Error.severity)
    )
    by_severity = {row[0]: row[1] for row in severity_result.all()}

    # Count by error_key using SQL GROUP BY
    error_key_result = await db.execute(
        select(Error.error_key, func.count(Error.id))
        .group_by(Error.error_key)
    )
    by_error_key = {row[0]: row[1] for row in error_key_result.all()}

    return ErrorStatsResponse(
        total_errors=total_errors,
        by_status=by_status,
        by_severity=by_severity,
        by_error_key=by_error_key,
    )


@router.get("/by-driver")
async def get_errors_by_driver(db: AsyncSession = Depends(get_db)):
    """
    Get error statistics grouped by driver.

    Returns:
        Results with error counts and recent errors for each driver
    """
    from sqlalchemy import case, literal_column
    from sqlalchemy.sql import label

    # Get aggregated stats per driver using SQL (much more efficient)
    stats_query = (
        select(
            Error.driver_id,
            func.max(Error.driver_name).label("driver_name"),
            func.max(Error.company_id).label("company_id"),
            func.max(Error.company_name).label("company_name"),
            func.count(Error.id).label("total_errors"),
            # Severity counts
            func.sum(case((Error.severity == "critical", 1), else_=0)).label("critical"),
            func.sum(case((Error.severity == "high", 1), else_=0)).label("high"),
            func.sum(case((Error.severity == "medium", 1), else_=0)).label("medium"),
            func.sum(case((Error.severity == "low", 1), else_=0)).label("low"),
            # Status counts
            func.sum(case((Error.status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((Error.status == "fixing", 1), else_=0)).label("fixing"),
            func.sum(case((Error.status == "fixed", 1), else_=0)).label("fixed"),
            func.sum(case((Error.status == "failed", 1), else_=0)).label("failed"),
        )
        .group_by(Error.driver_id)
        .order_by(func.count(Error.id).desc())
    )

    stats_result = await db.execute(stats_query)
    driver_stats = stats_result.all()

    # Build results with recent errors for each driver
    results = []
    for row in driver_stats:
        driver_id = row.driver_id

        # Get recent 10 errors for this driver (separate query, limited)
        recent_query = (
            select(Error)
            .where(Error.driver_id == driver_id)
            .order_by(Error.discovered_at.desc())
            .limit(10)
        )
        recent_result = await db.execute(recent_query)
        recent_errors = recent_result.scalars().all()

        results.append({
            "driver_id": driver_id,
            "driver_name": row.driver_name,
            "company_id": row.company_id,
            "company_name": row.company_name,
            "total_errors": row.total_errors,
            "by_severity": {
                "critical": row.critical or 0,
                "high": row.high or 0,
                "medium": row.medium or 0,
                "low": row.low or 0,
            },
            "by_status": {
                "pending": row.pending or 0,
                "fixing": row.fixing or 0,
                "fixed": row.fixed or 0,
                "failed": row.failed or 0,
            },
            "recent_errors": [
                {
                    "id": str(error.id),
                    "error_key": error.error_key,
                    "error_name": error.error_name,
                    "error_message": error.error_message,
                    "severity": error.severity,
                    "status": error.status,
                    "category": error.category,
                    "discovered_at": error.discovered_at.isoformat() if error.discovered_at else None,
                    "error_metadata": error.error_metadata,
                }
                for error in recent_errors
            ],
        })

    return {"results": results}


@router.get("/{error_id}", response_model=ErrorResponse)
async def get_error(error_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get a specific error by ID.

    Args:
        error_id: Error UUID

    Returns:
        Error details
    """
    result = await db.execute(
        select(Error).where(Error.id == error_id).options(selectinload(Error.fixes))
    )
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    return ErrorResponse.from_orm(error)


@router.patch("/{error_id}/status")
async def update_error_status(
    error_id: UUID, status: str, db: AsyncSession = Depends(get_db)
):
    """
    Update error status.

    Args:
        error_id: Error UUID
        status: New status (pending, fixing, fixed, failed, ignored)

    Returns:
        Updated error
    """
    valid_statuses = ["pending", "fixing", "fixed", "failed", "ignored"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    result = await db.execute(select(Error).where(Error.id == error_id))
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    error.status = status
    if status == "fixed":
        error.fixed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(error)

    logger.info(f"Error {error_id} status updated to '{status}'")

    return ErrorResponse.from_orm(error)


@router.delete("/{error_id}")
async def delete_error(error_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Delete an error (and its fixes due to CASCADE).

    Args:
        error_id: Error UUID

    Returns:
        Success message
    """
    result = await db.execute(select(Error).where(Error.id == error_id))
    error = result.scalar_one_or_none()

    if not error:
        raise HTTPException(status_code=404, detail="Error not found")

    await db.delete(error)
    await db.commit()

    logger.warning(f"Error {error_id} deleted")

    return {"message": "Error deleted successfully"}


@router.post("/refresh-names")
async def refresh_error_names(db: AsyncSession = Depends(get_db)):
    """
    Refresh driver and company names from Supabase for all errors.

    Returns:
        Number of errors updated
    """
    try:
        from ...supabase.client import get_supabase_client

        # Get all companies with drivers
        supabase = get_supabase_client()
        companies = await supabase.get_companies_with_drivers()

        # Build lookup maps
        company_names = {c.company_id: c.company_name for c in companies}
        driver_names = {}
        for company in companies:
            for driver in company.drivers:
                driver_names[driver.driver_id] = driver.driver_name

        # Get all errors
        result = await db.execute(select(Error))
        errors = result.scalars().all()

        updated_count = 0
        for error in errors:
            # Update company name
            if error.company_id in company_names:
                error.company_name = company_names[error.company_id]
                updated_count += 1

            # Update driver name
            if error.driver_id in driver_names:
                error.driver_name = driver_names[error.driver_id]

        await db.commit()

        logger.info(f"Refreshed names for {updated_count} errors")
        return {"message": f"Updated {updated_count} errors", "updated": updated_count}

    except Exception as e:
        logger.exception(f"Failed to refresh names: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh names: {str(e)}")

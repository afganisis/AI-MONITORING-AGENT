"""Fix management endpoints."""

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
from app.database.models import Fix, Error

router = APIRouter()


class FixResponse(BaseModel):
    """Fix response model."""

    id: str
    error_id: str
    strategy_name: str
    fix_description: Optional[str] = None
    api_calls: Optional[dict] = None
    status: str
    result_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    retries: int
    requires_approval: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FixWithErrorResponse(BaseModel):
    """Fix response with error details."""

    id: str
    error_id: str
    strategy_name: str
    fix_description: Optional[str] = None
    status: str
    requires_approval: bool
    created_at: datetime
    error: dict  # Simplified error info


class FixListResponse(BaseModel):
    """Paginated fix list response."""

    fixes: List[FixResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FixApprovalRequest(BaseModel):
    """Fix approval request."""

    approved_by: str


@router.get("/", response_model=FixListResponse)
async def list_fixes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    requires_approval: Optional[bool] = None,
    error_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of fixes with optional filters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        status: Filter by status (pending_approval, approved, executing, success, failed, rejected)
        requires_approval: Filter by requires_approval flag
        error_id: Filter by error ID

    Returns:
        Paginated list of fixes
    """
    # Build filters
    filters = []
    if status:
        filters.append(Fix.status == status)
    if requires_approval is not None:
        filters.append(Fix.requires_approval == requires_approval)
    if error_id:
        filters.append(Fix.error_id == error_id)

    # Get total count
    count_query = select(func.count(Fix.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Get paginated fixes
    offset = (page - 1) * page_size
    query = (
        select(Fix).order_by(Fix.created_at.desc()).offset(offset).limit(page_size)
    )
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    fixes = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return FixListResponse(
        fixes=[FixResponse.model_validate(fix) for fix in fixes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/pending-approvals")
async def get_pending_approvals(db: AsyncSession = Depends(get_db)):
    """
    Get all fixes pending approval.

    Returns:
        List of fixes awaiting approval with error details
    """
    result = await db.execute(
        select(Fix)
        .where(
            and_(
                Fix.status == "pending_approval",
                Fix.requires_approval == True,
            )
        )
        .options(selectinload(Fix.error))
        .order_by(Fix.created_at.desc())
    )
    fixes = result.scalars().all()

    response = []
    for fix in fixes:
        response.append(
            {
                "id": str(fix.id),
                "error_id": str(fix.error_id),
                "strategy_name": fix.strategy_name,
                "fix_description": fix.fix_description,
                "api_calls": fix.api_calls,
                "status": fix.status,
                "created_at": fix.created_at,
                "error": {
                    "id": str(fix.error.id),
                    "error_key": fix.error.error_key,
                    "error_name": fix.error.error_name,
                    "driver_name": fix.error.driver_name,
                    "severity": fix.error.severity,
                },
            }
        )

    return {"fixes": response, "total": len(response)}


@router.get("/{fix_id}", response_model=FixResponse)
async def get_fix(fix_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Get a specific fix by ID.

    Args:
        fix_id: Fix UUID

    Returns:
        Fix details
    """
    result = await db.execute(
        select(Fix).where(Fix.id == fix_id).options(selectinload(Fix.error))
    )
    fix = result.scalar_one_or_none()

    if not fix:
        raise HTTPException(status_code=404, detail="Fix not found")

    return FixResponse.model_validate(fix)


@router.post("/{fix_id}/approve")
async def approve_fix(
    fix_id: UUID, approval: FixApprovalRequest, db: AsyncSession = Depends(get_db)
):
    """
    Approve a fix for execution.

    Args:
        fix_id: Fix UUID
        approval: Approval details (who approved)

    Returns:
        Updated fix
    """
    result = await db.execute(select(Fix).where(Fix.id == fix_id))
    fix = result.scalar_one_or_none()

    if not fix:
        raise HTTPException(status_code=404, detail="Fix not found")

    if fix.status != "pending_approval":
        raise HTTPException(
            status_code=400, detail=f"Cannot approve fix with status '{fix.status}'"
        )

    fix.status = "approved"
    fix.approved_by = approval.approved_by
    fix.approved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(fix)

    logger.info(f"Fix {fix_id} approved by {approval.approved_by}")

    return FixResponse.model_validate(fix)


@router.post("/{fix_id}/reject")
async def reject_fix(
    fix_id: UUID, rejection: FixApprovalRequest, db: AsyncSession = Depends(get_db)
):
    """
    Reject a fix.

    Args:
        fix_id: Fix UUID
        rejection: Rejection details (who rejected)

    Returns:
        Updated fix
    """
    result = await db.execute(select(Fix).where(Fix.id == fix_id))
    fix = result.scalar_one_or_none()

    if not fix:
        raise HTTPException(status_code=404, detail="Fix not found")

    if fix.status != "pending_approval":
        raise HTTPException(
            status_code=400, detail=f"Cannot reject fix with status '{fix.status}'"
        )

    fix.status = "rejected"
    fix.approved_by = rejection.approved_by
    fix.approved_at = datetime.utcnow()
    fix.result_message = "Rejected by admin"

    await db.commit()
    await db.refresh(fix)

    logger.info(f"Fix {fix_id} rejected by {rejection.approved_by}")

    return FixResponse.model_validate(fix)


@router.delete("/{fix_id}")
async def delete_fix(fix_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Delete a fix.

    Args:
        fix_id: Fix UUID

    Returns:
        Success message
    """
    result = await db.execute(select(Fix).where(Fix.id == fix_id))
    fix = result.scalar_one_or_none()

    if not fix:
        raise HTTPException(status_code=404, detail="Fix not found")

    await db.delete(fix)
    await db.commit()

    logger.warning(f"Fix {fix_id} deleted")

    return {"message": "Fix deleted successfully"}


@router.get("/stats/summary")
async def get_fix_stats(db: AsyncSession = Depends(get_db)):
    """
    Get fix statistics.

    Returns:
        Aggregated statistics about fixes (optimized with SQL aggregation)
    """
    # Get total count efficiently
    total_result = await db.execute(select(func.count(Fix.id)))
    total_fixes = total_result.scalar_one()

    # Count by status using SQL GROUP BY
    status_result = await db.execute(
        select(Fix.status, func.count(Fix.id))
        .group_by(Fix.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Calculate success rate
    successful = by_status.get("success", 0)
    failed = by_status.get("failed", 0)
    total_completed = successful + failed
    success_rate = (successful / total_completed * 100) if total_completed > 0 else 0

    return {
        "total_fixes": total_fixes,
        "by_status": by_status,
        "success_rate": round(success_rate, 2),
        "pending_approvals": by_status.get("pending_approval", 0),
    }

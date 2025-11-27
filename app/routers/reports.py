from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import report_service
from app.services.auth_service import get_current_user
from app.models.user import User as ORMUser
from app.models.user_role import UserRole as ORMUserRole
from app.models.role import Role as ORMRole, RoleEnum
from app.schemas.report import (
    AssetReport,
    IncidentReport,
    ReportsOverview,
    FinancialReport,
    ActivityReport,
    SchoolsReport
)


router = APIRouter(prefix="/reports", tags=["reports"])


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_school_id(db: Session, user: ORMUser) -> Optional[UUID]:
    """
    Get the school_id for the current user if they are not a Super Admin.
    Returns None for Super Admins (they can see all schools).
    """
    # Check if user is Super Admin
    super_admin_role = db.query(ORMRole).filter(
        ORMRole.name == RoleEnum.SUPER_ADMIN
    ).first()

    if super_admin_role:
        user_has_super_admin = db.query(ORMUserRole).filter(
            ORMUserRole.user_id == user.id,
            ORMUserRole.role_id == super_admin_role.id
        ).first()

        if user_has_super_admin:
            return None  # Super Admin can see all schools

    # Get the first school for non-Super Admin users
    user_role = db.query(ORMUserRole).filter(
        ORMUserRole.user_id == user.id
    ).first()

    if user_role:
        return user_role.school_id

    return None


def apply_school_filter(
    db: Session,
    user: ORMUser,
    requested_school_id: Optional[UUID] = None
) -> Optional[UUID]:
    """
    Apply school filtering based on user role.

    - Super Admins can request any school_id or None (all schools)
    - Other users are restricted to their assigned school
    """
    user_school_id = get_user_school_id(db, user)

    # If user is Super Admin (user_school_id is None), use requested school_id
    if user_school_id is None:
        return requested_school_id

    # If user is not Super Admin, enforce their school_id
    # Ignore requested_school_id and use user's school
    return user_school_id


# ============================================================================
# Asset Report Endpoint
# ============================================================================

@router.get("/assets", response_model=AssetReport)
async def get_asset_report(
    start_date: Optional[str] = Query(None, description="Start date in ISO 8601 format (e.g., '2025-01-01')"),
    end_date: Optional[str] = Query(None, description="End date in ISO 8601 format"),
    preset: Optional[str] = Query(None, description="Preset range: today, week, month, quarter, year, all_time"),
    school_id: Optional[UUID] = Query(None, description="Filter by school ID (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: ORMUser = Depends(get_current_user)
):
    """
    Get comprehensive asset report with breakdowns by status, category, and school.

    **Date Filtering:**
    - Use `preset` for quick ranges (today, week, month, quarter, year, all_time)
    - Or use `start_date` and `end_date` for custom ranges
    - Default: last 30 days

    **Access Control:**
    - Super Admin: Can view all schools or filter by specific school
    - Other roles: Automatically filtered to their assigned school
    """
    # Apply school filtering based on user role
    effective_school_id = apply_school_filter(db, current_user, school_id)

    # Parse date range
    start_dt, end_dt = report_service.parse_date_range(start_date, end_date, preset)

    # Get report data
    report_data = report_service.get_asset_report(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
        school_id=effective_school_id
    )

    # Update date range info with preset if it was used
    report_data["date_range"]["preset"] = preset

    return AssetReport(**report_data)


# ============================================================================
# Incident Report Endpoint
# ============================================================================

@router.get("/incidents", response_model=IncidentReport)
async def get_incident_report(
    start_date: Optional[str] = Query(None, description="Start date in ISO 8601 format (e.g., '2025-01-01')"),
    end_date: Optional[str] = Query(None, description="End date in ISO 8601 format"),
    preset: Optional[str] = Query(None, description="Preset range: today, week, month, quarter, year, all_time"),
    school_id: Optional[UUID] = Query(None, description="Filter by school ID (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: ORMUser = Depends(get_current_user)
):
    """
    Get comprehensive incident analytics report including status breakdown,
    resolution times, and problematic assets.

    **Date Filtering:**
    - Use `preset` for quick ranges (today, week, month, quarter, year, all_time)
    - Or use `start_date` and `end_date` for custom ranges
    - Default: last 30 days

    **Access Control:**
    - Super Admin: Can view all schools or filter by specific school
    - Other roles: Automatically filtered to their assigned school
    """
    # Apply school filtering based on user role
    effective_school_id = apply_school_filter(db, current_user, school_id)

    # Parse date range
    start_dt, end_dt = report_service.parse_date_range(start_date, end_date, preset)

    # Get report data
    report_data = report_service.get_incident_report(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
        school_id=effective_school_id
    )

    # Update date range info with preset if it was used
    report_data["date_range"]["preset"] = preset

    return IncidentReport(**report_data)


# ============================================================================
# Overview Report Endpoint
# ============================================================================

@router.get("/overview", response_model=ReportsOverview)
async def get_reports_overview(
    start_date: Optional[str] = Query(None, description="Start date in ISO 8601 format (e.g., '2025-01-01')"),
    end_date: Optional[str] = Query(None, description="End date in ISO 8601 format"),
    preset: Optional[str] = Query(None, description="Preset range: today, week, month, quarter, year, all_time"),
    school_id: Optional[UUID] = Query(None, description="Filter by school ID (Super Admin only)"),
    db: Session = Depends(get_db),
    current_user: ORMUser = Depends(get_current_user)
):
    """
    Get comprehensive overview combining all available reports.

    This endpoint returns a complete snapshot of:
    - Asset statistics and breakdowns
    - Incident analytics and trends

    **Date Filtering:**
    - Use `preset` for quick ranges (today, week, month, quarter, year, all_time)
    - Or use `start_date` and `end_date` for custom ranges
    - Default: last 30 days

    **Access Control:**
    - Super Admin: Can view all schools or filter by specific school
    - Other roles: Automatically filtered to their assigned school
    """
    # Apply school filtering based on user role
    effective_school_id = apply_school_filter(db, current_user, school_id)

    # Parse date range
    start_dt, end_dt = report_service.parse_date_range(start_date, end_date, preset)

    # Get overview data
    overview_data = report_service.get_reports_overview(
        db=db,
        start_date=start_dt,
        end_date=end_dt,
        school_id=effective_school_id
    )

    # Update date range info with preset if it was used
    overview_data["assets"]["date_range"]["preset"] = preset
    overview_data["incidents"]["date_range"]["preset"] = preset

    return ReportsOverview(**overview_data)

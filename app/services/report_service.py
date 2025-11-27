from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, select, and_, or_, case
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List, Any

from app.models.asset import Asset, AssetTemplate, AssetCategory, AssetEvent
from app.models.incident import Incident
from app.models.classroom import Classroom
from app.models.school import School
from app.models.subscription import Subscription, Plan
from app.models.user import User


# ============================================================================
# Date Utility Functions
# ============================================================================

def get_date_preset(preset: str) -> Tuple[datetime, datetime]:
    """
    Convert a preset string to start and end datetime.

    Args:
        preset: One of 'today', 'week', 'month', 'quarter', 'year', 'all_time'

    Returns:
        Tuple of (start_date, end_date)
    """
    now = datetime.utcnow()
    end_date = now

    if preset == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif preset == "week":
        start_date = now - timedelta(days=7)
    elif preset == "month":
        start_date = now - timedelta(days=30)
    elif preset == "quarter":
        start_date = now - timedelta(days=90)
    elif preset == "year":
        start_date = now - timedelta(days=365)
    elif preset == "all_time":
        start_date = None
        end_date = None
    else:
        # Default to last 30 days
        start_date = now - timedelta(days=30)

    return start_date, end_date


def parse_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    preset: Optional[str] = None
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse date range from query parameters.
    Priority: preset > explicit dates > default (last 30 days)

    Args:
        start_date: ISO 8601 date string (e.g., "2025-01-01")
        end_date: ISO 8601 date string
        preset: Preset range ('today', 'week', 'month', 'quarter', 'year', 'all_time')

    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    # If preset is provided, use it
    if preset:
        return get_date_preset(preset)

    # If explicit dates are provided, parse them
    if start_date or end_date:
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # If parsing fails, ignore and use default
                pass

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # If we successfully parsed at least one date, return
        if start_dt or end_dt:
            return start_dt, end_dt

    # Default: last 30 days
    return get_date_preset("month")


# ============================================================================
# Asset Report Functions
# ============================================================================

def get_assets_by_status(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get asset count and total value grouped by status.
    """
    query = db.query(
        Asset.status,
        func.count(Asset.id).label('count'),
        func.coalesce(func.sum(Asset.value_estimate), 0).label('total_value')
    ).filter(Asset.deleted_at == None)

    # Apply date filter if provided (based on created_at)
    if start_date:
        query = query.filter(Asset.created_at >= start_date)
    if end_date:
        query = query.filter(Asset.created_at <= end_date)

    # Apply school filter if provided
    if school_id:
        query = query.join(Classroom).filter(Classroom.school_id == school_id)

    query = query.group_by(Asset.status)
    results = query.all()

    return [
        {
            "status": row.status,
            "count": row.count,
            "total_value": float(row.total_value)
        }
        for row in results
    ]


def get_assets_by_category(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get asset count and total value grouped by category.
    """
    # Query with left join to include assets without category
    query = db.query(
        AssetCategory.id.label('category_id'),
        func.coalesce(AssetCategory.name, 'Sin categoría').label('category_name'),
        func.count(Asset.id).label('count'),
        func.coalesce(func.sum(Asset.value_estimate), 0).label('total_value')
    ).select_from(Asset).outerjoin(
        AssetTemplate, Asset.template_id == AssetTemplate.id
    ).outerjoin(
        AssetCategory, AssetTemplate.category_id == AssetCategory.id
    ).filter(Asset.deleted_at == None)

    # Apply date filter
    if start_date:
        query = query.filter(Asset.created_at >= start_date)
    if end_date:
        query = query.filter(Asset.created_at <= end_date)

    # Apply school filter
    if school_id:
        query = query.join(Classroom, Asset.classroom_id == Classroom.id).filter(
            Classroom.school_id == school_id
        )

    query = query.group_by(AssetCategory.id, AssetCategory.name)
    results = query.all()

    return [
        {
            "category_id": row.category_id,
            "category_name": row.category_name,
            "count": row.count,
            "total_value": float(row.total_value)
        }
        for row in results
    ]


def get_assets_by_school(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get asset count and total value grouped by school.
    """
    query = db.query(
        School.id.label('school_id'),
        School.name.label('school_name'),
        func.count(Asset.id).label('count'),
        func.coalesce(func.sum(Asset.value_estimate), 0).label('total_value')
    ).select_from(Asset).join(
        Classroom, Asset.classroom_id == Classroom.id
    ).join(
        School, Classroom.school_id == School.id
    ).filter(
        Asset.deleted_at == None,
        School.deleted_at == None
    )

    # Apply date filter
    if start_date:
        query = query.filter(Asset.created_at >= start_date)
    if end_date:
        query = query.filter(Asset.created_at <= end_date)

    # Apply school filter
    if school_id:
        query = query.filter(School.id == school_id)

    query = query.group_by(School.id, School.name)
    results = query.all()

    return [
        {
            "school_id": row.school_id,
            "school_name": row.school_name,
            "count": row.count,
            "total_value": float(row.total_value)
        }
        for row in results
    ]


def get_top_valued_assets(
    db: Session,
    limit: int = 10,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get top assets by value.
    """
    query = db.query(
        Asset.id,
        AssetTemplate.name.label('template_name'),
        Asset.serial_number,
        Asset.value_estimate,
        Asset.status,
        Asset.classroom_id
    ).outerjoin(
        AssetTemplate, Asset.template_id == AssetTemplate.id
    ).filter(
        Asset.deleted_at == None,
        Asset.value_estimate != None
    )

    # Apply school filter
    if school_id:
        query = query.join(Classroom).filter(Classroom.school_id == school_id)

    query = query.order_by(Asset.value_estimate.desc()).limit(limit)
    results = query.all()

    return [
        {
            "id": row.id,
            "template_name": row.template_name,
            "serial_number": row.serial_number,
            "value_estimate": float(row.value_estimate) if row.value_estimate else None,
            "status": row.status,
            "classroom_id": row.classroom_id
        }
        for row in results
    ]


def get_asset_report(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Generate complete asset report with all breakdowns.
    """
    # Get total count and value
    total_query = db.query(
        func.count(Asset.id).label('total_assets'),
        func.coalesce(func.sum(Asset.value_estimate), 0).label('total_value')
    ).filter(Asset.deleted_at == None)

    # Apply filters
    if start_date:
        total_query = total_query.filter(Asset.created_at >= start_date)
    if end_date:
        total_query = total_query.filter(Asset.created_at <= end_date)
    if school_id:
        total_query = total_query.join(Classroom).filter(Classroom.school_id == school_id)

    totals = total_query.first()

    # Get assets without template count
    no_template_query = db.query(
        func.count(Asset.id)
    ).filter(
        Asset.deleted_at == None,
        Asset.template_id == None
    )

    if start_date:
        no_template_query = no_template_query.filter(Asset.created_at >= start_date)
    if end_date:
        no_template_query = no_template_query.filter(Asset.created_at <= end_date)
    if school_id:
        no_template_query = no_template_query.join(Classroom).filter(Classroom.school_id == school_id)

    no_template_count = no_template_query.scalar() or 0

    # Get all breakdowns
    by_status = get_assets_by_status(db, start_date, end_date, school_id)
    by_category = get_assets_by_category(db, start_date, end_date, school_id)
    by_school = get_assets_by_school(db, start_date, end_date, school_id)
    top_assets = get_top_valued_assets(db, limit=10, school_id=school_id)

    return {
        "total_assets": totals.total_assets,
        "total_value": float(totals.total_value),
        "by_status": by_status,
        "by_category": by_category,
        "by_school": by_school,
        "assets_without_template": no_template_count,
        "top_valued_assets": top_assets,
        "date_range": {
            "start": start_date,
            "end": end_date,
            "preset": None
        },
        "generated_at": datetime.utcnow()
    }


# ============================================================================
# Incident Report Functions
# ============================================================================

def calculate_average_resolution_time(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> Optional[float]:
    """
    Calculate average resolution time in hours for resolved incidents.
    """
    query = db.query(
        func.avg(
            func.extract('epoch', Incident.resolved_at - Incident.reported_at) / 3600
        ).label('avg_hours')
    ).filter(
        Incident.resolved_at != None
    )

    # Apply date filter (based on reported_at)
    if start_date:
        query = query.filter(Incident.reported_at >= start_date)
    if end_date:
        query = query.filter(Incident.reported_at <= end_date)

    # Apply school filter through asset and classroom
    if school_id:
        query = query.join(Asset, Incident.asset_id == Asset.id).join(
            Classroom, Asset.classroom_id == Classroom.id
        ).filter(Classroom.school_id == school_id)

    result = query.scalar()
    return float(result) if result else None


def get_incidents_by_status(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get incident count grouped by status.
    """
    query = db.query(
        Incident.status,
        func.count(Incident.id).label('count')
    )

    # Apply date filter
    if start_date:
        query = query.filter(Incident.reported_at >= start_date)
    if end_date:
        query = query.filter(Incident.reported_at <= end_date)

    # Apply school filter
    if school_id:
        query = query.join(Asset, Incident.asset_id == Asset.id).join(
            Classroom, Asset.classroom_id == Classroom.id
        ).filter(Classroom.school_id == school_id)

    query = query.group_by(Incident.status)
    results = query.all()

    return [
        {
            "status": row.status,
            "count": row.count
        }
        for row in results
    ]


def get_unresolved_incidents_count(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> int:
    """
    Get count of unresolved incidents (open or in_progress).
    """
    query = db.query(
        func.count(Incident.id)
    ).filter(
        Incident.status.in_(['open', 'in_progress'])
    )

    # Apply date filter
    if start_date:
        query = query.filter(Incident.reported_at >= start_date)
    if end_date:
        query = query.filter(Incident.reported_at <= end_date)

    # Apply school filter
    if school_id:
        query = query.join(Asset, Incident.asset_id == Asset.id).join(
            Classroom, Asset.classroom_id == Classroom.id
        ).filter(Classroom.school_id == school_id)

    return query.scalar() or 0


def get_recent_incidents(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 20,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get recent incidents in date range.
    """
    query = db.query(Incident).filter()

    # Apply date filter
    if start_date:
        query = query.filter(Incident.reported_at >= start_date)
    if end_date:
        query = query.filter(Incident.reported_at <= end_date)

    # Apply school filter
    if school_id:
        query = query.join(Asset, Incident.asset_id == Asset.id).join(
            Classroom, Asset.classroom_id == Classroom.id
        ).filter(Classroom.school_id == school_id)

    query = query.order_by(Incident.reported_at.desc()).limit(limit)
    incidents = query.all()

    return [
        {
            "id": incident.id,
            "asset_id": incident.asset_id,
            "description": incident.description,
            "status": incident.status,
            "reported_at": incident.reported_at,
            "resolved_at": incident.resolved_at,
            "reported_by": incident.reported_by
        }
        for incident in incidents
    ]


def get_top_assets_with_incidents(
    db: Session,
    limit: int = 10,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Get assets with most incidents.
    """
    query = db.query(
        Asset.id.label('asset_id'),
        AssetTemplate.name.label('template_name'),
        Asset.serial_number,
        func.count(Incident.id).label('incident_count')
    ).join(
        Incident, Asset.id == Incident.asset_id
    ).outerjoin(
        AssetTemplate, Asset.template_id == AssetTemplate.id
    )

    # Apply date filter
    if start_date:
        query = query.filter(Incident.reported_at >= start_date)
    if end_date:
        query = query.filter(Incident.reported_at <= end_date)

    # Apply school filter
    if school_id:
        query = query.join(Classroom, Asset.classroom_id == Classroom.id).filter(
            Classroom.school_id == school_id
        )

    query = query.group_by(
        Asset.id, AssetTemplate.name, Asset.serial_number
    ).order_by(
        func.count(Incident.id).desc()
    ).limit(limit)

    results = query.all()

    return [
        {
            "asset_id": row.asset_id,
            "template_name": row.template_name,
            "serial_number": row.serial_number,
            "incident_count": row.incident_count
        }
        for row in results
    ]


def get_incident_report(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Generate complete incident analytics report.
    """
    # Get total count
    total_query = db.query(func.count(Incident.id))

    if start_date:
        total_query = total_query.filter(Incident.reported_at >= start_date)
    if end_date:
        total_query = total_query.filter(Incident.reported_at <= end_date)
    if school_id:
        total_query = total_query.join(Asset, Incident.asset_id == Asset.id).join(
            Classroom, Asset.classroom_id == Classroom.id
        ).filter(Classroom.school_id == school_id)

    total_incidents = total_query.scalar() or 0

    # Get all metrics
    by_status = get_incidents_by_status(db, start_date, end_date, school_id)
    avg_resolution = calculate_average_resolution_time(db, start_date, end_date, school_id)
    unresolved_count = get_unresolved_incidents_count(db, start_date, end_date, school_id)
    recent = get_recent_incidents(db, start_date, end_date, limit=20, school_id=school_id)
    top_assets = get_top_assets_with_incidents(db, limit=10, start_date=start_date, end_date=end_date, school_id=school_id)

    return {
        "total_incidents": total_incidents,
        "by_status": by_status,
        "average_resolution_hours": avg_resolution,
        "unresolved_count": unresolved_count,
        "recent_incidents": recent,
        "top_assets_with_incidents": top_assets,
        "date_range": {
            "start": start_date,
            "end": end_date,
            "preset": None
        },
        "generated_at": datetime.utcnow()
    }


# ============================================================================
# Comprehensive Overview Function
# ============================================================================

def get_reports_overview(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    school_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive overview combining assets and incidents reports.
    """
    asset_report = get_asset_report(db, start_date, end_date, school_id)
    incident_report = get_incident_report(db, start_date, end_date, school_id)

    return {
        "assets": asset_report,
        "incidents": incident_report,
        "generated_at": datetime.utcnow()
    }

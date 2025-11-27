from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Date Range Schemas
# ============================================================================

class DateRangeInfo(BaseModel):
    """Information about the date range used in the report"""
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    preset: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Asset Report Schemas
# ============================================================================

class AssetStatusBreakdown(BaseModel):
    """Asset count and value grouped by status"""
    status: str
    count: int
    total_value: float = Field(default=0.0)

    class Config:
        from_attributes = True


class AssetCategoryBreakdown(BaseModel):
    """Asset count and value grouped by category"""
    category_id: Optional[UUID] = None
    category_name: str
    count: int
    total_value: float = Field(default=0.0)

    class Config:
        from_attributes = True


class AssetSchoolBreakdown(BaseModel):
    """Asset count and value grouped by school"""
    school_id: UUID
    school_name: str
    count: int
    total_value: float = Field(default=0.0)

    class Config:
        from_attributes = True


class TopAssetItem(BaseModel):
    """Individual asset information for top valued assets"""
    id: UUID
    template_name: Optional[str] = None
    serial_number: Optional[str] = None
    value_estimate: Optional[float] = None
    status: str
    classroom_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class AssetReport(BaseModel):
    """Complete asset report with breakdowns and statistics"""
    total_assets: int
    total_value: float
    by_status: List[AssetStatusBreakdown]
    by_category: List[AssetCategoryBreakdown]
    by_school: List[AssetSchoolBreakdown] = Field(default_factory=list)
    assets_without_template: int = 0
    top_valued_assets: List[TopAssetItem] = Field(default_factory=list)
    date_range: DateRangeInfo
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# Incident Report Schemas
# ============================================================================

class IncidentStatusBreakdown(BaseModel):
    """Incident count grouped by status"""
    status: str
    count: int

    class Config:
        from_attributes = True


class IncidentSummary(BaseModel):
    """Summary information for a single incident"""
    id: UUID
    asset_id: UUID
    description: str
    status: str
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    reported_by: UUID

    class Config:
        from_attributes = True


class AssetIncidentCount(BaseModel):
    """Asset with its incident count"""
    asset_id: UUID
    template_name: Optional[str] = None
    serial_number: Optional[str] = None
    incident_count: int

    class Config:
        from_attributes = True


class IncidentReport(BaseModel):
    """Complete incident analytics report"""
    total_incidents: int
    by_status: List[IncidentStatusBreakdown]
    average_resolution_hours: Optional[float] = None
    unresolved_count: int = 0
    recent_incidents: List[IncidentSummary] = Field(default_factory=list)
    top_assets_with_incidents: List[AssetIncidentCount] = Field(default_factory=list)
    date_range: DateRangeInfo
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# Financial Report Schemas
# ============================================================================

class CategoryValue(BaseModel):
    """Value breakdown by category"""
    category_id: Optional[UUID] = None
    category_name: str
    total_value: float

    class Config:
        from_attributes = True


class SchoolValue(BaseModel):
    """Value breakdown by school"""
    school_id: UUID
    school_name: str
    total_value: float

    class Config:
        from_attributes = True


class FinancialReport(BaseModel):
    """Financial overview report"""
    total_inventory_value: float
    value_by_category: List[CategoryValue] = Field(default_factory=list)
    value_by_school: List[SchoolValue] = Field(default_factory=list)
    active_subscriptions: int = 0
    expired_subscriptions: int = 0
    monthly_recurring_revenue: float = 0.0
    date_range: DateRangeInfo
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# Activity Report Schemas
# ============================================================================

class AssetEventSummary(BaseModel):
    """Summary of an asset event"""
    id: UUID
    asset_id: UUID
    user_id: Optional[UUID] = None
    event_type: str
    timestamp: datetime
    asset_metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class UserActivity(BaseModel):
    """User activity summary"""
    user_id: UUID
    user_name: str
    event_count: int

    class Config:
        from_attributes = True


class ActivityReport(BaseModel):
    """Activity and events report"""
    recent_asset_events: List[AssetEventSummary] = Field(default_factory=list)
    assets_created_count: int = 0
    incidents_created_count: int = 0
    active_users_count: int = 0
    top_active_users: List[UserActivity] = Field(default_factory=list)
    date_range: DateRangeInfo
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# Schools Report Schemas
# ============================================================================

class ClassroomSummary(BaseModel):
    """Summary of a classroom with asset statistics"""
    id: UUID
    name: str
    code: str
    asset_count: int = 0
    total_value: float = 0.0

    class Config:
        from_attributes = True


class SchoolSummary(BaseModel):
    """Summary of a school with classroom and asset statistics"""
    id: UUID
    name: str
    classroom_count: int = 0
    asset_count: int = 0
    total_value: float = 0.0
    classrooms: List[ClassroomSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SchoolsReport(BaseModel):
    """Complete schools and classrooms report"""
    total_schools: int
    schools: List[SchoolSummary]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


# ============================================================================
# Comprehensive Overview Schema
# ============================================================================

class ReportsOverview(BaseModel):
    """Comprehensive overview combining all report types"""
    assets: AssetReport
    incidents: IncidentReport
    financial: Optional[FinancialReport] = None
    activity: Optional[ActivityReport] = None
    schools: Optional[SchoolsReport] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

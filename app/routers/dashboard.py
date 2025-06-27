from uuid import UUID
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

# Schema Imports
from app.models.user import UserRead
from app.schemas.school import SchoolRead
from app.schemas.classroom import ClassroomRead
from app.schemas.asset import AssetRead, AssetTemplateRead, AssetCategoryShallowRead
from app.schemas.incident import IncidentRead
from app.schemas.qr import QRCodeRead
# ORM Models
from app.models.user import User as ORMUser
from app.models.user_role import UserRole as ORMUserRole
from app.models.role import Role as ORMRole, RoleEnum

# Services
from app.core.database import get_db
from app.services import dashboard_service
from app.services.auth_service import get_current_user

# --- Pydantic Schemas for Dashboard Response ---

class DashboardUserRole(BaseModel):
    role_name: str
    school_name: Optional[str] = None

    class Config:
        from_attributes = True

class DashboardUser(UserRead):
    assigned_roles: List[DashboardUserRole]

    class Config:
        from_attributes = True

class DashboardData(BaseModel):
    users: List[DashboardUser]
    schools: List[SchoolRead]
    classrooms: List[ClassroomRead]
    asset_templates: List[AssetTemplateRead]
    assets: List[AssetRead]
    incidents: List[IncidentRead]

    class Config:
        from_attributes = True

# --- Dependency to Ensure SUPER_ADMIN Access ---

async def get_current_super_admin_user(
    current_user: ORMUser = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> ORMUser:
    super_admin_role = db.execute(
        select(ORMRole).where(ORMRole.name == RoleEnum.SUPER_ADMIN)
    ).scalars().first()

    if not super_admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration error: SUPER_ADMIN role not found."
        )

    user_has_role = db.execute(
        select(ORMUserRole).where(
            ORMUserRole.user_id == current_user.id,
            ORMUserRole.role_id == super_admin_role.id
        )
    ).scalars().first()

    if not user_has_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource. Requires SUPER_ADMIN role."
        )

    return current_user

# --- Router and Endpoint ---

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/", response_model=DashboardData)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    super_admin: ORMUser = Depends(get_current_super_admin_user)
) -> DashboardData:
    
    data_dict = dashboard_service.get_dashboard_data(db=db)

    dashboard_users = []
    for user in data_dict["users"]:
        assigned_roles = []

        if hasattr(user, 'roles'):
            for ur in user.roles:
                role_name = ur.role.name if ur.role else "Unknown Role"
                school_name = ur.school.name if ur.school else None
                assigned_roles.append(DashboardUserRole(role_name=role_name, school_name=school_name))

        dashboard_users.append(
            DashboardUser(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                status=user.status,
                created_at=user.created_at,
                assigned_roles=assigned_roles
            )
        )

    return DashboardData(
    users=dashboard_users,
    schools=[SchoolRead.from_orm(s) for s in data_dict["schools"]],
    classrooms=[ClassroomRead.from_orm(c) for c in data_dict["classrooms"]],
    asset_templates=[
        AssetTemplateRead(
            id=at.id,
            name=at.name,
            description=at.description,
            manufacturer=at.manufacturer,
            model_number=at.model_number,
            category_id=at.category_id,
            created_at=at.created_at,
            updated_at=at.updated_at,
            category=AssetCategoryShallowRead.from_orm(at.category) if at.category else None
        )
        for at in data_dict["asset_templates"]
    ],
assets=[
    AssetRead(
        id=a.id,
        template_id=a.template_id,
        serial_number=a.serial_number,
        purchase_date=a.purchase_date,
        value_estimate=a.value_estimate,
        image_url=a.image_url,
        status=a.status,
        classroom_id=a.classroom_id,
        created_at=a.created_at,
        updated_at=a.updated_at,
        template=AssetTemplateRead.from_orm(a.template) if a.template else None,
        qr_code=QRCodeRead.from_orm(a.qr_code) if a.qr_code else None
    )
    for a in data_dict["assets"]
],
    incidents=[IncidentRead.from_orm(i) for i in data_dict["incidents"]],
)
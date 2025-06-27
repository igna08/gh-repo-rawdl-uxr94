from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.models.user import User
from app.models.user_role import UserRole # For relationship loading
from app.models.role import Role # For relationship loading
from app.models.school import School
from app.models.classroom import Classroom
from app.models.asset import AssetTemplate, Asset # AssetTemplate is in asset.py
from app.models.incident import Incident


def get_dashboard_data(db: Session) -> dict:
    """
    Retrieves all data for the admin dashboard.
    Fetches users (with roles and schools), schools, classrooms,
    asset templates, assets, and incidents.
    """

    # 1. Fetch Users with their roles and schools
    users_stmt = (
        select(User)
        .options(
            selectinload(User.roles)  # Assuming User.user_roles is the relationship to UserRole
            .selectinload(UserRole.role),  # Then UserRole.role for Role
            selectinload(User.roles)
            .selectinload(UserRole.school) # Then UserRole.school for School
        )
    )
    users = db.execute(users_stmt).scalars().unique().all()

    # 2. Fetch Schools
    schools_stmt = select(School)
    schools = db.execute(schools_stmt).scalars().all()

    # 3. Fetch Classrooms
    classrooms_stmt = select(Classroom)
    classrooms = db.execute(classrooms_stmt).scalars().all()

    # 4. Fetch Asset Templates
    asset_templates_stmt = select(AssetTemplate)
    asset_templates = db.execute(asset_templates_stmt).scalars().all()

    # 5. Fetch Assets
    assets_stmt = select(Asset)
    assets = db.execute(assets_stmt).scalars().all()

    # 6. Fetch Incidents
    incidents_stmt = select(Incident)
    incidents = db.execute(incidents_stmt).scalars().all()

    return {
        "users": users,
        "schools": schools,
        "classrooms": classrooms,
        "asset_templates": asset_templates,
        "assets": assets,
        "incidents": incidents,
    }

from uuid import UUID
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.classroom import ClassroomCreate, ClassroomRead, ClassroomUpdate
from app.services import classroom_service, school_service
from app.models.classroom import Classroom as ClassroomModel # For response_model
from app.models.asset import Asset, AssetTemplate, AssetCategory

router = APIRouter()

@router.post(
    "/schools/{school_id}/classrooms/",
    response_model=ClassroomRead,
    status_code=status.HTTP_201_CREATED,
    tags=["classrooms"],
    summary="Create a new classroom for a specific school",
)
def create_classroom_for_school(
    classroom: ClassroomCreate,
    school_id: UUID = Path(..., description="The ID of the school to create the classroom in"),
    db: Session = Depends(get_db),
):
    # Verify school exists
    db_school = school_service.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=404, detail=f"School with id {school_id} not found")
    
    created_classroom = classroom_service.create_classroom(db=db, classroom=classroom, school_id=school_id)
    if created_classroom is None: # Should ideally be handled by specific exceptions in service
        raise HTTPException(status_code=400, detail="Could not create classroom, possibly due to school not found or code generation issues.")
    return created_classroom

@router.get(
    "/schools/{school_id}/classrooms/",
    response_model=List[ClassroomRead],
    tags=["classrooms"],
    summary="Get classrooms for a specific school",
)
def read_classrooms_for_school(
    school_id: UUID = Path(..., description="The ID of the school"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # Verify school exists
    db_school = school_service.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=404, detail=f"School with id {school_id} not found")
    
    classrooms = classroom_service.get_classrooms_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return classrooms

@router.get(
    "/classrooms/",
    response_model=List[ClassroomRead],
    tags=["classrooms (admin)"],
    summary="Get all classrooms (admin)",
)
def read_all_classrooms(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    classrooms = classroom_service.get_all_classrooms(db, skip=skip, limit=limit)
    return classrooms

@router.get(
    "/classrooms/{classroom_id}",
    response_model=ClassroomRead,
    tags=["classrooms"],
    summary="Get a specific classroom by ID",
)
def read_classroom(
    classroom_id: UUID = Path(..., description="The ID of the classroom"),
    db: Session = Depends(get_db),
):
    db_classroom = classroom_service.get_classroom(db, classroom_id=classroom_id)
    if db_classroom is None:
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found")
    return db_classroom

@router.put(
    "/classrooms/{classroom_id}",
    response_model=ClassroomRead,
    tags=["classrooms"],
    summary="Update a classroom",
)
def update_existing_classroom(
    classroom_in: ClassroomUpdate,
    classroom_id: UUID = Path(..., description="The ID of the classroom to update"),
    db: Session = Depends(get_db),
):
    db_classroom = classroom_service.update_classroom(db, classroom_id=classroom_id, classroom_in=classroom_in)
    if db_classroom is None:
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found for updating")
    return db_classroom

@router.delete(
    "/classrooms/{classroom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["classrooms"],
    summary="Delete a classroom",
)
def delete_existing_classroom(
    classroom_id: UUID = Path(..., description="The ID of the classroom to delete"),
    db: Session = Depends(get_db),
):
    db_classroom = classroom_service.delete_classroom(db, classroom_id=classroom_id)
    if db_classroom is None: # Or if it was already deleted and service returns None
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found for deletion")
    return None

# --- Asset Inventory for Classroom ---

class AssetGroupItem(BaseModel):
    template_name: str
    category_name: Optional[str] = None
    status: str
    value_estimate: Optional[float] = None
    quantity: int
    total_value: Optional[float] = None
    asset_ids: List[UUID]

class ClassroomInventoryResponse(BaseModel):
    classroom_id: UUID
    classroom_name: str
    classroom_code: str
    school_id: UUID
    assets: List[AssetGroupItem]
    total_assets: int
    total_value: float

@router.get(
    "/classrooms/{classroom_id}/inventory",
    response_model=ClassroomInventoryResponse,
    tags=["classrooms"],
    summary="Get detailed inventory of classroom assets",
)
def get_classroom_inventory(
    classroom_id: UUID = Path(..., description="The ID of the classroom to get inventory for"),
    db: Session = Depends(get_db),
):
    """
    Get a detailed inventory of all assets in a classroom, grouped by template/type.
    Shows quantity, total value, and other details for each asset type.

    Example response shows assets grouped by template with:
    - Template/asset name
    - Category
    - Status
    - Individual value
    - Quantity (number of assets of this type)
    - Total value (quantity * individual value)
    """
    # Verify classroom exists
    db_classroom = classroom_service.get_classroom(db, classroom_id=classroom_id)
    if not db_classroom:
        raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found")

    # Get all assets for this classroom (excluding deleted ones)
    assets = db.query(Asset).filter(
        Asset.classroom_id == classroom_id,
        Asset.deleted_at == None
    ).all()

    # Group assets by template_id and status
    asset_groups: Dict[tuple, Dict[str, Any]] = {}

    for asset in assets:
        # Get template name
        template_name = "Sin template"
        category_name = None

        if asset.template_id and asset.template:
            template_name = asset.template.name
            if asset.template.category:
                category_name = asset.template.category.name

        # Create grouping key (template_id, status)
        group_key = (str(asset.template_id) if asset.template_id else "no_template", asset.status)

        if group_key not in asset_groups:
            asset_groups[group_key] = {
                "template_name": template_name,
                "category_name": category_name,
                "status": asset.status,
                "value_estimate": float(asset.value_estimate) if asset.value_estimate else None,
                "quantity": 0,
                "total_value": 0.0,
                "asset_ids": []
            }

        # Increment quantity
        asset_groups[group_key]["quantity"] += 1
        asset_groups[group_key]["asset_ids"].append(asset.id)

        # Add to total value
        if asset.value_estimate:
            asset_groups[group_key]["total_value"] += float(asset.value_estimate)

    # Convert to list
    grouped_assets = [AssetGroupItem(**group_data) for group_data in asset_groups.values()]

    # Calculate totals
    total_assets = len(assets)
    total_value = sum(float(asset.value_estimate) for asset in assets if asset.value_estimate) or 0.0

    return ClassroomInventoryResponse(
        classroom_id=db_classroom.id,
        classroom_name=db_classroom.name,
        classroom_code=db_classroom.code,
        school_id=db_classroom.school_id,
        assets=grouped_assets,
        total_assets=total_assets,
        total_value=total_value
    )

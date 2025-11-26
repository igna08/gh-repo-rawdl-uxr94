from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.asset import ( # Grouped imports
    AssetCreate, AssetRead, AssetUpdate, AssetEventRead,
    AssetCategoryCreate, AssetCategoryRead,
    AssetTemplateCreate, AssetTemplateRead
)
from app.services import asset_service
from app.models.asset import Asset as AssetModel, AssetCategory as AssetCategoryModel, AssetTemplate as AssetTemplateModel
from app.routers.dashboard import get_current_super_admin_user # Added
from app.models.user import User as ORMUser # Added
from pydantic import BaseModel

async def get_current_user_id() -> UUID:
    # In a real app, this would come from an authentication token
    # For now, returning a fixed UUID for testing purposes
    # Ensure this user exists in your DB if your service layer performs checks
    # Or handle it as an optional user for some operations if applicable
    return UUID("97f45c67-5c74-493d-bcb6-757c5253d0a1") # Dummy User ID


router = APIRouter(
    prefix="/assets",
    tags=["assets"],
    responses={404: {"description": "Not found"}},
)

# --- AssetCategory Endpoints ---

@router.post("/categories/", response_model=AssetCategoryRead, status_code=status.HTTP_201_CREATED, tags=["asset_categories"])
def create_new_asset_category(
    category_in: AssetCategoryCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    try:
        created_category = asset_service.create_asset_category(db=db, category_in=category_in)
        # Convierte el modelo ORM a Pydantic
        return AssetCategoryRead.from_orm(created_category)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
@router.put("/categories/{category_id}", response_model=AssetCategoryRead, tags=["asset_categories"])
def update_asset_category(
    category_id: UUID = Path(..., description="The ID of the asset category to update"),
    category_data: AssetCategoryCreate = Body(..., description="Updated asset category data"),
    db: Session = Depends(get_db)
):
    db_category = asset_service.get_asset_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset category not found")

    db_category.name = category_data.name
    db_category.description = category_data.description
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["asset_categories"])
def delete_asset_category(
    category_id: UUID = Path(..., description="The ID of the asset category to delete"),
    db: Session = Depends(get_db)
):
    db_category = asset_service.get_asset_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset category not found")

    db.delete(db_category)
    db.commit()
    return


@router.get("/categories/", response_model=List[AssetCategoryRead], tags=["asset_categories"])
def read_all_asset_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    categories = asset_service.get_all_asset_categories(db, skip=skip, limit=limit)
    return categories

# --- AssetTemplate Endpoints ---

@router.post("/templates/", response_model=AssetTemplateRead, status_code=status.HTTP_201_CREATED, tags=["asset_templates"])
def create_new_asset_template(
    template_in: AssetTemplateCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    try:
        created_template = asset_service.create_asset_template(db=db, template_in=template_in, current_user_id=current_user_id)
        return created_template
    except ValueError as e: # Handles invalid category_id or other value errors from service
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/templates/{template_id}", response_model=AssetTemplateRead, tags=["asset_templates"])
def read_single_asset_template(
    template_id: UUID = Path(..., description="The ID of the asset template to retrieve"),
    db: Session = Depends(get_db)
):
    db_template = asset_service.get_asset_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset template not found")
    return db_template

@router.get("/templates/", response_model=List[AssetTemplateRead], tags=["asset_templates"])
def read_all_asset_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    templates = asset_service.get_all_asset_templates(db, skip=skip, limit=limit)
    return templates

@router.get("/templates/by_category/{category_id}", response_model=List[AssetTemplateRead], tags=["asset_templates"])
def read_asset_templates_for_category(
    category_id: UUID = Path(..., description="The ID of the category to retrieve asset templates for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Optional: Check if category exists first, or let service handle it (service currently doesn't explicitly check category existence for this call)
    # For consistency, one might add a check here or ensure service layer does.
    # db_category = asset_service.get_asset_category(db, category_id=category_id)
    # if not db_category:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} not found")
    templates = asset_service.get_asset_templates_by_category(db, category_id=category_id, skip=skip, limit=limit)
    # If templates list is empty, it could be no templates for that category, or category doesn't exist.
    # Depending on desired API behavior, further checks could be added.
    return templates

# --- Asset Endpoints ---

@router.post("/", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_new_asset(
    asset_in: AssetCreate, 
    db: Session = Depends(get_db),
    current_admin_user: ORMUser = Depends(get_current_super_admin_user)
):
    try:
        created_asset = asset_service.create_asset(db=db, asset_in=asset_in, current_user_id=current_admin_user.id)
    except ValueError as e: # Catch specific errors from service layer
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if created_asset is None: # Should be covered by specific exceptions ideally
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Asset could not be created.")
    return created_asset

@router.get("/", response_model=List[AssetRead])
def read_all_assets(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    assets = asset_service.get_all_assets(db, skip=skip, limit=limit)
    return assets

@router.get("/by_classroom/{classroom_id}", response_model=List[AssetRead])
def read_assets_for_classroom(
    classroom_id: UUID = Path(..., description="The ID of the classroom to retrieve assets for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Optional: Check if classroom exists first, or let service handle it
    # db_classroom = classroom_service.get_classroom(db, classroom_id) # Assuming classroom_service is available
    # if not db_classroom:
    #     raise HTTPException(status_code=404, detail=f"Classroom with id {classroom_id} not found")
    assets = asset_service.get_assets_by_classroom(db, classroom_id=classroom_id, skip=skip, limit=limit)
    return assets


@router.get("/{asset_id}", response_model=AssetRead)
def read_single_asset(
    asset_id: UUID = Path(..., description="The ID of the asset to retrieve"),
    db: Session = Depends(get_db)
):
    db_asset = asset_service.get_asset(db, asset_id=asset_id)
    if db_asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return db_asset

@router.put("/{asset_id}", response_model=AssetRead)
def update_existing_asset(
    asset_id: UUID = Path(..., description="The ID of the asset to update"),
    asset_in: AssetUpdate = Body(...),
    db: Session = Depends(get_db),
    current_admin_user: ORMUser = Depends(get_current_super_admin_user)
):
    try:
        updated_asset = asset_service.update_asset(db, asset_id=asset_id, asset_in=asset_in, current_user_id=current_admin_user.id)
    except ValueError as e: # Catch specific errors from service layer
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    if updated_asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found or update failed")
    return updated_asset

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_single_asset(
    asset_id: UUID = Path(..., description="The ID of the asset to delete"),
    db: Session = Depends(get_db),
    current_admin_user: ORMUser = Depends(get_current_super_admin_user)
):
    deleted_asset = asset_service.delete_asset(db, asset_id=asset_id, current_user_id=current_admin_user.id)
    if deleted_asset is None: # Could mean already deleted or not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found or already deleted")
    return None

@router.get("/{asset_id}/events/", response_model=List[AssetEventRead])
def read_asset_event_history(
    asset_id: UUID = Path(..., description="The ID of the asset to retrieve its event history"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Optional: Check if asset exists first
    # db_asset = asset_service.get_asset(db, asset_id=asset_id)
    # if db_asset is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    events = asset_service.get_asset_events(db, asset_id=asset_id, skip=skip, limit=limit)
    if not events and not asset_service.get_asset(db, asset_id=asset_id): # if no events AND asset doesnt exist
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found or no events for this asset.")
    return events

# --- New Endpoints for Additional Functionality ---

class ImageUpdateRequest(BaseModel):
    image_url: str

@router.patch("/{asset_id}/image", response_model=AssetRead, summary="Update asset image")
def update_asset_image(
    asset_id: UUID = Path(..., description="The ID of the asset to update the image for"),
    image_data: ImageUpdateRequest = Body(...),
    db: Session = Depends(get_db),
    current_admin_user: ORMUser = Depends(get_current_super_admin_user)
):
    """
    Update the image URL for a specific asset.
    This endpoint allows updating only the image without modifying other asset properties.
    """
    db_asset = asset_service.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    asset_update = AssetUpdate(image_url=image_data.image_url)
    updated_asset = asset_service.update_asset(db, asset_id=asset_id, asset_in=asset_update, current_user_id=current_admin_user.id)

    return updated_asset

class BulkDeleteRequest(BaseModel):
    asset_ids: List[UUID]

@router.post("/bulk-delete", status_code=status.HTTP_200_OK, summary="Delete multiple assets")
def bulk_delete_assets(
    delete_request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_admin_user: ORMUser = Depends(get_current_super_admin_user)
):
    """
    Delete multiple assets at once by providing a list of asset IDs.
    Returns the count of successfully deleted assets.
    """
    deleted_count = 0
    errors = []

    for asset_id in delete_request.asset_ids:
        try:
            deleted_asset = asset_service.delete_asset(db, asset_id=asset_id, current_user_id=current_admin_user.id)
            if deleted_asset:
                deleted_count += 1
            else:
                errors.append({"asset_id": str(asset_id), "error": "Asset not found or already deleted"})
        except Exception as e:
            errors.append({"asset_id": str(asset_id), "error": str(e)})

    return {
        "deleted_count": deleted_count,
        "total_requested": len(delete_request.asset_ids),
        "errors": errors if errors else None
    }

class BulkUpdateRequest(BaseModel):
    asset_ids: List[UUID]
    value_estimate: Optional[float] = None
    status: Optional[str] = None
    image_url: Optional[str] = None

@router.patch("/bulk-update", status_code=status.HTTP_200_OK, summary="Update multiple assets")
def bulk_update_assets(
    update_request: BulkUpdateRequest,
    db: Session = Depends(get_db),
    current_admin_user: ORMUser = Depends(get_current_super_admin_user)
):
    """
    Update multiple assets at once. You can update value_estimate, status, or image_url.
    All specified fields will be applied to all assets in the list.
    """
    updated_count = 0
    errors = []

    # Prepare update data
    update_data = AssetUpdate(
        value_estimate=update_request.value_estimate,
        status=update_request.status,
        image_url=update_request.image_url
    )

    for asset_id in update_request.asset_ids:
        try:
            updated_asset = asset_service.update_asset(
                db,
                asset_id=asset_id,
                asset_in=update_data,
                current_user_id=current_admin_user.id
            )
            if updated_asset:
                updated_count += 1
            else:
                errors.append({"asset_id": str(asset_id), "error": "Asset not found"})
        except Exception as e:
            errors.append({"asset_id": str(asset_id), "error": str(e)})

    return {
        "updated_count": updated_count,
        "total_requested": len(update_request.asset_ids),
        "errors": errors if errors else None
    }

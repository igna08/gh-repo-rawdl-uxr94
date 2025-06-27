from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.asset import Asset, AssetEvent, AssetStatusEnum, AssetCategory, AssetTemplate # Added AssetTemplate
from app.schemas.asset import AssetCreate, AssetUpdate, AssetEventCreate, AssetCategoryCreate, AssetTemplateCreate # Added AssetTemplateCreate
from app.models.classroom import Classroom # For checking classroom_id existence
# from app.models.user import User # For created_by_id, user_id in events
from app.services import qr_service # Import qr_service

# --- AssetCategory Service Functions ---

def create_asset_category(db: Session, category_in: AssetCategoryCreate) -> AssetCategory:
    """
    Creates a new asset category.
    """
    db_category = AssetCategory(**category_in.model_dump())
    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Asset category with name '{category_in.name}' already exists.")

def get_asset_category(db: Session, category_id: UUID) -> AssetCategory | None:
    """
    Retrieves an asset category by its ID.
    """
    return db.query(AssetCategory).filter(AssetCategory.id == category_id).first()

def get_asset_category_by_name(db: Session, category_name: str) -> AssetCategory | None:
    """
    Retrieves an asset category by its name.
    """
    return db.query(AssetCategory).filter(AssetCategory.name == category_name).first()

def get_all_asset_categories(db: Session, skip: int = 0, limit: int = 100) -> List[AssetCategory]:
    """
    Retrieves all asset categories with pagination.
    """
    return db.query(AssetCategory).offset(skip).limit(limit).all()

# --- AssetTemplate Service Functions ---

def create_asset_template(db: Session, template_in: AssetTemplateCreate, current_user_id: UUID) -> AssetTemplate: # Assuming current_user_id might be used for logging or ownership in future
    """
    Creates a new asset template.
    Validates if the provided category_id exists.
    """
    if template_in.category_id:
        category = db.query(AssetCategory).filter(AssetCategory.id == template_in.category_id).first()
        if not category:
            raise ValueError(f"Asset category with id {template_in.category_id} not found.")

    db_template = AssetTemplate(**template_in.model_dump())
    # db_template.created_by_id = current_user_id # Example if you add created_by_id to AssetTemplate model
    try:
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except IntegrityError: # Catch potential unique constraint violations or other DB issues
        db.rollback()
        # Be more specific with error message if possible, e.g. unique name for template if that's a constraint
        raise ValueError(f"Asset template with name '{template_in.name}' may already exist or other integrity error.")

def get_asset_template(db: Session, template_id: UUID) -> AssetTemplate | None:
    """
    Retrieves an asset template by its ID.
    """
    return db.query(AssetTemplate).filter(AssetTemplate.id == template_id).first()

def get_all_asset_templates(db: Session, skip: int = 0, limit: int = 100) -> List[AssetTemplate]:
    """
    Retrieves all asset templates with pagination.
    """
    return db.query(AssetTemplate).offset(skip).limit(limit).all()

def get_asset_templates_by_category(db: Session, category_id: UUID, skip: int = 0, limit: int = 100) -> List[AssetTemplate]:
    """
    Retrieves all asset templates for a given category_id with pagination.
    """
    return db.query(AssetTemplate).filter(AssetTemplate.category_id == category_id).offset(skip).limit(limit).all()

# --- AssetEvent Service Functions --- (Adjusted to keep log_asset_event with Asset related services)
# Helper function to log asset events
def log_asset_event(
    db: Session, 
    asset_id: UUID, 
    event_type: str, 
    user_id: Optional[UUID],  # User ID can be None for system events
    metadata: Optional[Dict[str, Any]] = None
) -> AssetEvent:
    event_data = AssetEventCreate(asset_id=asset_id, user_id=user_id, event_type=event_type, metadata=metadata)
    db_event = AssetEvent(
        asset_id=event_data.asset_id,
        user_id=event_data.user_id,
        event_type=event_data.event_type,
        metadata=event_data.metadata,
        timestamp=datetime.utcnow() # Ensure timestamp is set here
    )
    db.add(db_event)
    # db.commit() # Decide on commit strategy: commit per event or per main operation
    # db.refresh(db_event) # Refresh if ID or other server-defaults are needed immediately
    return db_event

# --- Asset Service Functions ---

def create_asset(db: Session, asset_in: AssetCreate, current_user_id: UUID) -> Asset:
    # Validate classroom_id if necessary
    db_classroom = db.query(Classroom).filter(Classroom.id == asset_in.classroom_id, Classroom.deleted_at == None).first()
    if not db_classroom:
        raise ValueError(f"Classroom with id {asset_in.classroom_id} not found.")

    # Convert template_id string to UUID if it's provided, assuming it's a UUID string
    template_uuid = None
    if asset_in.template_id:
        try:
            template_uuid = asset_in.template_id
        except ValueError:
            raise ValueError(f"Invalid template_id format: {asset_in.template_id}. Must be a valid UUID string.")
            # Optionally, look up AssetTemplate by a string name/code if that's the design

    asset_data = asset_in.model_dump(exclude={"template_id"})
    # Convierte image_url a string si existe
    if asset_data.get("image_url") is not None:
        asset_data["image_url"] = str(asset_data["image_url"])

    db_asset = Asset(
        **asset_data,
        template_id=template_uuid,
        created_by_id=current_user_id
    )
    db.add(db_asset)
    db.flush() # Flush to get db_asset.id for the event logging and QR code creation

    log_asset_event(db, asset_id=db_asset.id, event_type="asset_created", user_id=current_user_id, metadata={
        "classroom_id": str(asset_in.classroom_id),
        "serial_number": asset_in.serial_number
    })
    
    # Automatically create a QR code for the new asset
    qr_service.create_qr_code_for_asset(db=db, asset=db_asset)
    # The commit for qr_service happens within that function if successful,
    # or could be part of a larger transaction managed here.
    # For now, create_qr_code_for_asset handles its own commit.

    db.commit() # Commit asset creation and event log
    db.refresh(db_asset) # Refresh to get updated state including any relationships populated by QR service (if any)
    return db_asset

def get_asset(db: Session, asset_id: UUID) -> Asset | None:
    return db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at == None).first()

def get_assets_by_classroom(db: Session, classroom_id: UUID, skip: int = 0, limit: int = 100) -> List[Asset]:
    return db.query(Asset).filter(Asset.classroom_id == classroom_id, Asset.deleted_at == None).offset(skip).limit(limit).all()

def get_all_assets(db: Session, skip: int = 0, limit: int = 100) -> List[Asset]:
    return db.query(Asset).filter(Asset.deleted_at == None).offset(skip).limit(limit).all()

def update_asset(db: Session, asset_id: UUID, asset_in: AssetUpdate, current_user_id: UUID) -> Asset | None:
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None

    update_data = asset_in.model_dump(exclude_unset=True)
    changes = {}

    for key, value in update_data.items():
        old_value = getattr(db_asset, key)
        if old_value != value:
            changes[key] = {"old": str(old_value), "new": str(value)} # Log changes
            setattr(db_asset, key, value)
    
    if "template_id" in update_data and update_data["template_id"] is not None:
        try:
            setattr(db_asset, "template_id", UUID(update_data["template_id"]))
        except ValueError:
             raise ValueError(f"Invalid template_id format: {update_data['template_id']}. Must be a valid UUID string.")


    if changes:
        db_asset.updated_at = datetime.utcnow()
        log_asset_event(
            db, 
            asset_id=db_asset.id, 
            event_type="asset_updated", 
            user_id=current_user_id, 
            metadata={"changes": changes}
        )
        db.commit()
        db.refresh(db_asset)
    return db_asset

def delete_asset(db: Session, asset_id: UUID, current_user_id: UUID) -> Asset | None:
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    if db_asset.deleted_at is None: # Check if not already soft-deleted
        db_asset.deleted_at = datetime.utcnow()
        db_asset.status = AssetStatusEnum.decommissioned # Or a 'deleted' status if preferred
        
        log_asset_event(
            db, 
            asset_id=db_asset.id, 
            event_type="asset_deleted", 
            user_id=current_user_id,
            metadata={"status_changed_to": AssetStatusEnum.decommissioned.value}
        )
        db.commit()
        db.refresh(db_asset)
    return db_asset

def get_asset_events(db: Session, asset_id: UUID, skip: int = 0, limit: int = 100) -> List[AssetEvent]:
    # First, check if asset exists to avoid querying events for a non-existent/deleted asset if that's desired behavior
    # asset = get_asset(db, asset_id)
    # if not asset:
    #     return [] # Or raise HTTPException(status_code=404, detail="Asset not found")

    return db.query(AssetEvent).filter(AssetEvent.asset_id == asset_id).order_by(AssetEvent.timestamp.desc()).offset(skip).limit(limit).all()

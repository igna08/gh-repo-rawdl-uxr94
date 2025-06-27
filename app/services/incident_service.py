from uuid import UUID
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.incident import Incident, IncidentStatusEnum
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.asset_service import log_asset_event # For logging events to asset history
from app.models.asset import Asset as AssetModel # For type hinting
from app.services.asset_service import get_asset # To check if asset exists

def create_incident(db: Session, incident_in: IncidentCreate, current_user_id: UUID) -> Incident:
    # Verify asset exists
    db_asset = get_asset(db, incident_in.asset_id)
    if not db_asset:
        raise ValueError(f"Asset with id {incident_in.asset_id} not found.")

    db_incident = Incident(
        asset_id=incident_in.asset_id,
        description=incident_in.description,
        photo_url=incident_in.photo_url,
        reported_by=current_user_id,
        status=IncidentStatusEnum.open # Initial status
    )
    db.add(db_incident)
    db.flush() # To get incident_id for event logging

    # Log an event for the associated asset
    log_asset_event(
        db=db,
        asset_id=incident_in.asset_id,
        event_type="incident_reported",
        user_id=current_user_id,
        metadata={
            "incident_id": str(db_incident.id),
            "description": db_incident.description,
            "status": db_incident.status.value
        }
    )
    
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_incident(db: Session, incident_id: UUID) -> Incident | None:
    return db.query(Incident).filter(Incident.id == incident_id).first()

def get_incidents_by_asset(db: Session, asset_id: UUID, skip: int = 0, limit: int = 100) -> List[Incident]:
    return db.query(Incident).filter(Incident.asset_id == asset_id).order_by(Incident.reported_at.desc()).offset(skip).limit(limit).all()

def get_all_incidents(db: Session, skip: int = 0, limit: int = 100) -> List[Incident]:
    return db.query(Incident).order_by(Incident.reported_at.desc()).offset(skip).limit(limit).all()

def update_incident(db: Session, incident_id: UUID, incident_in: IncidentUpdate, current_user_id: UUID) -> Incident | None:
    db_incident = get_incident(db, incident_id)
    if not db_incident:
        return None

    update_data = incident_in.model_dump(exclude_unset=True)
    logged_changes = {}

    for key, value in update_data.items():
        old_value = getattr(db_incident, key)
        # Special handling for enum status
        if key == "status" and isinstance(old_value, IncidentStatusEnum):
            old_value_str = old_value.value
        else:
            old_value_str = str(old_value)

        if old_value_str != value: # Compare string representations for logging
            logged_changes[key] = {"old": old_value_str, "new": value}
            setattr(db_incident, key, value)

    if "status" in update_data:
        new_status_val = update_data["status"]
        # Check if string value is valid for enum
        if not any(s.value == new_status_val for s in IncidentStatusEnum):
            raise ValueError(f"Invalid status value: {new_status_val}")
        
        new_status_enum = IncidentStatusEnum(new_status_val)
        setattr(db_incident, "status", new_status_enum) # Set as enum object

        if new_status_enum in [IncidentStatusEnum.resolved, IncidentStatusEnum.closed] and db_incident.resolved_at is None:
            db_incident.resolved_at = datetime.utcnow()
            if "resolved_at" not in logged_changes: # Ensure it's logged if not already by direct update
                 logged_changes["resolved_at"] = {"old": "None", "new": db_incident.resolved_at.isoformat()}

    if logged_changes:
        db_incident.updated_at = datetime.utcnow() # Manually update timestamp
        
        log_asset_event(
            db=db,
            asset_id=db_incident.asset_id,
            event_type="incident_updated", # Or more specific like "incident_status_changed"
            user_id=current_user_id,
            metadata={
                "incident_id": str(db_incident.id),
                "changes": logged_changes
            }
        )
        db.commit()
        db.refresh(db_incident)
        
    return db_incident

def delete_incident(db: Session, incident_id: UUID, current_user_id: UUID) -> Incident | None:
    # For now, implementing hard delete. If soft delete is needed, add a 'deleted_at' field to Incident model.
    db_incident = get_incident(db, incident_id)
    if not db_incident:
        return None

    asset_id = db_incident.asset_id # Store asset_id before deleting incident
    
    # Log an event for the associated asset
    log_asset_event(
        db=db,
        asset_id=asset_id, 
        event_type="incident_deleted",
        user_id=current_user_id,
        metadata={
            "incident_id": str(db_incident.id),
            "description": db_incident.description
        }
    )
    
    db.delete(db_incident)
    db.commit()
    # db_incident object is no longer valid here, so returning it might not be standard.
    # Often, delete operations return None or the deleted object's ID, or just a success status.
    # Returning the object as is (before it's expunged from session) if that's the pattern.
    return db_incident # Note: after commit, this object might be in a transient state or detached.
                        # For consistency, it might be better to return a representation or None.
                        # For this task, returning the object as requested. Consider implications.

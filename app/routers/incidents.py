from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.services import incident_service, asset_service # asset_service for asset existence check
from app.models.incident import Incident as IncidentModel # For response_model typing

# Placeholder for current_user_id dependency - replace with actual auth dependency later
async def get_current_user_id() -> UUID:
    # In a real app, this would come from an authentication token
    # For now, returning a fixed UUID for testing purposes
    # Ensure this user exists in your DB if your service layer performs checks
    return UUID("97f45c67-5c74-493d-bcb6-757c5253d0a1") # Dummy User ID

router = APIRouter(
    tags=["incidents"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/incidents/", 
    response_model=IncidentRead, 
    status_code=status.HTTP_201_CREATED,
    summary="Report a new incident"
)
def create_new_incident(
    incident_in: IncidentCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    try:
        created_incident = incident_service.create_incident(
            db=db, incident_in=incident_in, current_user_id=current_user_id
        )
    except ValueError as e: # Catch specific errors from service layer (e.g., asset not found)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if created_incident is None: # General fallback
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incident could not be created.")
    return created_incident

@router.get(
    "/incidents/", 
    response_model=List[IncidentRead],
    summary="Get all incidents"
)
def read_all_incidents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    incidents = incident_service.get_all_incidents(db, skip=skip, limit=limit)
    return incidents

@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentRead,
    summary="Get a specific incident by its ID"
)
def read_single_incident(
    incident_id: UUID = Path(..., description="The ID of the incident to retrieve"),
    db: Session = Depends(get_db),
):
    db_incident = incident_service.get_incident(db, incident_id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return db_incident

@router.put(
    "/incidents/{incident_id}",
    response_model=IncidentRead,
    summary="Update an existing incident"
)
def update_existing_incident(
    incident_id: UUID = Path(..., description="The ID of the incident to update"),
    incident_in: IncidentUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    try:
        updated_incident = incident_service.update_incident(
            db, incident_id=incident_id, incident_in=incident_in, current_user_id=current_user_id
        )
    except ValueError as e: # Catch specific errors like invalid status
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if updated_incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found or update failed")
    return updated_incident

@router.delete(
    "/incidents/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident"
)
def delete_single_incident(
    incident_id: UUID = Path(..., description="The ID of the incident to delete"),
    db: Session = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    # The service function currently returns the deleted object or None if not found.
    # For a 204 response, we don't return content.
    deleted_incident = incident_service.delete_incident(db, incident_id=incident_id, current_user_id=current_user_id)
    if deleted_incident is None: # Service returns None if not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return None # Explicitly return None for 204


@router.get(
    "/assets/{asset_id}/incidents/",
    response_model=List[IncidentRead],
    summary="Get all incidents for a specific asset"
)
def read_incidents_for_asset(
    asset_id: UUID = Path(..., description="The ID of the asset to retrieve incidents for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    # Optional: Check if asset exists first, or let service handle if needed.
    # For now, assuming asset_service.get_asset would be called if strict validation is needed here.
    # The incident_service.get_incidents_by_asset will return empty list if asset has no incidents or does not exist.
    # To provide a 404 if asset itself doesn't exist:
    db_asset = asset_service.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset with ID {asset_id} not found.")
        
    incidents = incident_service.get_incidents_by_asset(db, asset_id=asset_id, skip=skip, limit=limit)
    return incidents

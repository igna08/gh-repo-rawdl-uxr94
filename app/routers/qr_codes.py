from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.qr import QRCodeRead
from app.services import qr_service, asset_service # asset_service for checking asset existence
from app.models.qr import QRCode as QRCodeModel # For response_model typing

# Placeholder for current_user_id dependency - replace with actual auth dependency later
async def get_current_user_id() -> Optional[UUID]:
    # In a real app, this would come from an authentication token
    # For now, returning a fixed UUID or None
    return UUID("97f45c67-5c74-493d-bcb6-757c5253d0a1") # Dummy User ID

router = APIRouter(
    tags=["qr_codes"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/assets/{asset_id}/qr-codes/",
    response_model=QRCodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate or Regenerate QR Code for an Asset",
)
def generate_or_regenerate_asset_qr_code(
    asset_id: UUID = Path(..., description="The ID of the asset for which to generate/regenerate the QR code"),
    db: Session = Depends(get_db),
    # current_user_id: Optional[UUID] = Depends(get_current_user_id) # If user context is needed
):
    # Check if asset exists
    db_asset = asset_service.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset with id {asset_id} not found.")
    
    # Use the regenerate function which handles both creation and update
    qr_code = qr_service.regenerate_qr_code_for_asset(db, asset_id=asset_id)
    if not qr_code:
        # This case should ideally be handled by specific exceptions in service
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate or regenerate QR code.")
    return qr_code

@router.get(
    "/assets/{asset_id}/qr-codes/",
    response_model=QRCodeRead,
    summary="Get QR Code for an Asset",
)
def get_asset_qr_code(
    asset_id: UUID = Path(..., description="The ID of the asset to retrieve the QR code for"),
    db: Session = Depends(get_db),
):
    # Check if asset exists first (optional, service might also do this)
    db_asset = asset_service.get_asset(db, asset_id=asset_id)
    if not db_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset with id {asset_id} not found.")

    qr_code = qr_service.get_qr_code_by_asset_id(db, asset_id=asset_id)
    if qr_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR Code not found for this asset. Consider generating one first.")
    return qr_code

@router.get(
    "/qr-codes/{qr_code_id}",
    response_model=QRCodeRead,
    summary="Get QR Code by its ID",
)
def get_qr_code_by_qr_id(
    qr_code_id: UUID = Path(..., description="The ID of the QR code to retrieve"),
    db: Session = Depends(get_db),
):
    qr_code = qr_service.get_qr_code_by_id(db, qr_code_id=qr_code_id)
    if qr_code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR Code not found.")
    return qr_code

import qrcode
import io
import base64
import json
from uuid import UUID
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.qr import QRCode
from app.models.asset import Asset as AssetModel # To type hint asset parameter
from app.schemas.qr import QRCodeCreate # Though not directly used if asset is passed

# Configuration for QR code URL (replace with actual domain/config)
BASE_APP_URL = "https://yourapp.com" 
def get_asset(db: Session, asset_id: UUID) -> AssetModel | None:
    return db.query(AssetModel).filter(AssetModel.id == asset_id, AssetModel.deleted_at == None).first()

def generate_qr_code_image_base64(data: Dict[str, Any]) -> str:
    """
    Generates a QR code image from data and returns it as a base64 encoded PNG.
    """
    payload_str = json.dumps(data, sort_keys=True) # Ensure consistent payload string
    img = qrcode.make(payload_str)
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

def create_qr_code_for_asset(db: Session, asset: AssetModel) -> QRCode:
    """
    Creates a QR code record for a given asset.
    If a QR code already exists for the asset, it returns the existing one (or could update it).
    """
    # Check if QR code already exists for this asset
    existing_qr = db.query(QRCode).filter(QRCode.asset_id == asset.id).first()
    if existing_qr:
        # Optionally, update the existing QR code if payload/URL structure changed
        # For now, just return the existing one
        return existing_qr

    payload = {
        "asset_id": str(asset.id),
        "asset_url": f"{BASE_APP_URL}/assets/{asset.id}" 
        # Add other relevant info if needed, e.g., asset.serial_number
    }
    
    qr_code_image_str = generate_qr_code_image_base64(payload)
    
    db_qr_code = QRCode(
        asset_id=asset.id,
        qr_url=qr_code_image_str,
        payload=payload
    )
    
    try:
        db.add(db_qr_code)
        db.commit()
        db.refresh(db_qr_code)
    except IntegrityError: # Handles race condition if another session created it
        db.rollback()
        existing_qr = db.query(QRCode).filter(QRCode.asset_id == asset.id).first()
        if existing_qr:
            return existing_qr
        else: # Should not happen if IntegrityError was due to unique constraint on asset_id
            raise 
    
    return db_qr_code

def get_qr_code_by_asset_id(db: Session, asset_id: UUID) -> QRCode | None:
    """
    Retrieves QR code details for a given asset ID.
    """
    return db.query(QRCode).filter(QRCode.asset_id == asset_id).first()

def get_qr_code_by_id(db: Session, qr_code_id: UUID) -> QRCode | None:
    """
    Retrieves QR code by its own ID.
    """
    return db.query(QRCode).filter(QRCode.id == qr_code_id).first()

def regenerate_qr_code_for_asset(db: Session, asset_id: UUID) -> QRCode | None:
    """
    Regenerates QR code for an asset. If one exists, it's updated. If not, it's created.
    """
    asset = get_asset(db, asset_id) # Use asset_service to get the asset
    if not asset:
        return None # Or raise Exception("Asset not found")

    payload = {
        "asset_id": str(asset.id),
        "asset_url": f"{BASE_APP_URL}/assets/{asset.id}"
    }
    qr_code_image_str = generate_qr_code_image_base64(payload)

    existing_qr = db.query(QRCode).filter(QRCode.asset_id == asset.id).first()
    if existing_qr:
        existing_qr.qr_url = qr_code_image_str
        existing_qr.payload = payload
        db_qr_code = existing_qr
    else:
        db_qr_code = QRCode(
            asset_id=asset.id,
            qr_url=qr_code_image_str,
            payload=payload
        )
        db.add(db_qr_code)
    
    db.commit()
    db.refresh(db_qr_code)
    return db_qr_code

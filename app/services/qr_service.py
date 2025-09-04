import qrcode
import io
import base64
from uuid import UUID
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.qr import QRCode
from app.models.asset import Asset as AssetModel
from app.schemas.qr import QRCodeCreate

# Configuration for QR code URL (replace with actual domain/config)
BASE_APP_URL = "https://issa-qr.vercel.app" 

def get_asset(db: Session, asset_id: UUID) -> AssetModel | None:
    return db.query(AssetModel).filter(AssetModel.id == asset_id, AssetModel.deleted_at == None).first()

def generate_qr_code_image_base64(url: str) -> str:
    """
    Generates a QR code image from URL string and returns it as a base64 encoded PNG.
    Optimized for easy scanning with minimal error correction and simpler design.
    """
    # Create QR code instance with optimized settings for URLs
    qr = qrcode.QRCode(
        version=1,  # Start with smallest version, auto-adjusts if needed
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Low error correction for simpler pattern
        box_size=10,  # Size of each box in pixels
        border=4,  # Minimum border size
    )
    
    # Add only the URL data (much simpler than JSON)
    qr.add_data(url)
    qr.make(fit=True)  # Auto-adjust version if needed
    
    # Create image with high contrast
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

def create_qr_code_for_asset(db: Session, asset: AssetModel) -> QRCode:
    """
    Creates a QR code record for a given asset.
    QR code contains only the direct URL to the asset.
    """
    # Check if QR code already exists for this asset
    existing_qr = db.query(QRCode).filter(QRCode.asset_id == asset.id).first()
    if existing_qr:
        return existing_qr

    # Create simple URL (no JSON payload)
    asset_url = f"{BASE_APP_URL}/assets/{asset.id}"
    
    # Generate QR code with just the URL
    qr_code_image_str = generate_qr_code_image_base64(asset_url)

    # Store minimal payload for reference
    payload = {
        "asset_id": str(asset.id),
        "asset_url": asset_url
    }

    db_qr_code = QRCode(
        asset_id=asset.id,
        qr_url=qr_code_image_str,
        payload=payload  # Keep for database record, but QR contains only URL
    )

    try:
        db.add(db_qr_code)
        db.commit()
        db.refresh(db_qr_code)
    except IntegrityError:
        db.rollback()
        existing_qr = db.query(QRCode).filter(QRCode.asset_id == asset.id).first()
        if existing_qr:
            return existing_qr
        else:
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
    Regenerates QR code for an asset with optimized settings.
    """
    asset = get_asset(db, asset_id)
    if not asset:
        return None

    # Create simple URL
    asset_url = f"{BASE_APP_URL}/assets/{asset.id}"
    
    # Generate optimized QR code
    qr_code_image_str = generate_qr_code_image_base64(asset_url)
    
    # Update payload
    payload = {
        "asset_id": str(asset.id),
        "asset_url": asset_url
    }

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
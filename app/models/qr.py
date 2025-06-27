from sqlalchemy import Column, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
# Ensure Asset model is available for relationship reference, even if defined in another file.
# from app.models.asset import Asset # This import might cause circular dependency if Asset also imports QRCode.
# SQLAlchemy handles string references for relationships to avoid this.

class QRCode(Base):
    __tablename__ = "qr_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Ensure one-to-one relationship with Asset: asset_id is unique
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Stores the generated QR code, e.g., as a base64 data URI or a URL to an image file
    qr_url = Column(String, nullable=False) 
    
    # Stores the actual data embedded in the QR code (e.g., asset ID, URL to asset details)
    payload = Column(JSON, nullable=False)

    # Relationship to the Asset model
    # The `Asset` model should have a corresponding `qr_code = relationship("QRCode", back_populates="asset", uselist=False)`
    asset = relationship("Asset", back_populates="qr_code")

    def __repr__(self):
        return f"<QRCode id={self.id} asset_id={self.asset_id}>"

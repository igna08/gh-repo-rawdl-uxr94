import enum
from sqlalchemy import Column, ForeignKey, String, DateTime, Date, Enum, Text, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class AssetStatus(str, enum.Enum):
    operational = "operational"
    decommissioned = "decommissioned"
    # Added from schema for more detailed status
    available = "available" 
    in_repair = "in_repair"
    missing = "missing"

class AssetStatusEnum(str, enum.Enum):
    available = "available"
    in_repair = "in_repair"
    missing = "missing"
    decommissioned = "decommissioned"
    operational = "operational" # Original value, kept for compatibility if used

class AssetCategory(Base):
    __tablename__ = "asset_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)
    
    templates = relationship("AssetTemplate", back_populates="category") # Corrected relationship name
    
    def __repr__(self):
        return f"AssetCategory(id={self.id}, name='{self.name}')"

class AssetTemplate(Base):
    __tablename__ = "asset_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("asset_categories.id"), nullable=True)
    manufacturer = Column(String, nullable=True)
    model_number = Column(String, nullable=True)

    category = relationship("AssetCategory", back_populates="templates") # Corrected relationship name
    assets = relationship("Asset", back_populates="template")

    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)

    def __repr__(self):
        return f"AssetTemplate(id={self.id}, name='{self.name}')"

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("asset_templates.id"), nullable=True)
    # Assuming 'users.id' exists for created_by_id
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) 
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True)

    serial_number = Column(String, nullable=True, index=True)
    purchase_date = Column(Date, nullable=True)
    value_estimate = Column(Numeric(10, 2), nullable=True)
    image_url = Column(String, nullable=True)
    status = Column(Enum(AssetStatusEnum), default=AssetStatusEnum.available, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True) # For soft delete

    template = relationship("AssetTemplate", back_populates="assets")
    classroom = relationship("Classroom", back_populates="assets")
    # Placeholder for User relationship, actual User model might have a different back_populates name
    created_by = relationship("User", foreign_keys=[created_by_id]) 
    events = relationship("AssetEvent", back_populates="asset", cascade="all, delete-orphan")
    # Relationship to QRCode model (assuming it will be created later)
    qr_code = relationship("QRCode", back_populates="asset", uselist=False, cascade="all, delete-orphan") 

    def __repr__(self):
        return f"Asset(id={self.id}, serial_number='{self.serial_number}')"

class AssetEvent(Base):
    __tablename__ = "asset_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    # Assuming 'users.id' exists for user_id
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) 
    
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", nullable=False)
    asset_metadata = Column(JSON, nullable=True)

    asset = relationship("Asset", back_populates="events")
    # Placeholder for User relationship
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"AssetEvent(id={self.id}, asset_id='{self.asset_id}', event_type='{self.event_type}')"
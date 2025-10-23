import enum
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, String, DateTime, Date, Enum, Text, Numeric, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class AssetStatusEnum(str, enum.Enum):
    available = "available"
    in_repair = "in_repair"
    missing = "missing"
    decommissioned = "decommissioned"
    operational = "operational"

class AssetCategory(Base):
    __tablename__ = "asset_categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)
    templates = relationship("AssetTemplate", back_populates="category")

class AssetTemplate(Base):
    __tablename__ = "asset_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("asset_categories.id"), nullable=True)
    manufacturer = Column(String, nullable=True)
    model_number = Column(String, nullable=True)

    category = relationship("AssetCategory", back_populates="templates")
    assets = relationship("Asset", back_populates="template")

    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("asset_templates.id"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    classroom_id = Column(UUID(as_uuid=True), ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True)
    serial_number = Column(String, nullable=True, index=True)
    purchase_date = Column(Date, nullable=True)
    value_estimate = Column(Numeric(10, 2), nullable=True)
    image_url = Column(String, nullable=True)
    status = Column(Enum(AssetStatusEnum), default=AssetStatusEnum.available, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    template = relationship("AssetTemplate", back_populates="assets")
    classroom = relationship("Classroom", back_populates="assets")
    created_by = relationship("User", foreign_keys=[created_by_id])
    events = relationship("AssetEvent", back_populates="asset", cascade="all, delete-orphan")

class AssetEvent(Base):
    __tablename__ = "asset_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", nullable=False)
    metadata = Column(JSON, nullable=True)  # ✅ Este campo debe ser un dict, no MetaData()

    asset = relationship("Asset", back_populates="events")
    user = relationship("User", foreign_keys=[user_id])

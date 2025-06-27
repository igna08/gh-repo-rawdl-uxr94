import enum
from sqlalchemy import Column, ForeignKey, String, DateTime, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base
# Assuming User and Asset models are defined elsewhere and will be correctly related.
# from app.models.asset import Asset
# from app.models.user import User


class IncidentStatusEnum(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(IncidentStatusEnum, name="incident_status_enum"), nullable=False, default=IncidentStatusEnum.open)
    
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps for record updates (optional, but good practice)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow)

    # Relationships
    asset = relationship("Asset") # Add back_populates in Asset model: incidents = relationship("Incident", back_populates="asset")
    reporter = relationship("User") # Add back_populates in User model: reported_incidents = relationship("Incident", back_populates="reporter")

    def __repr__(self):
        return f"<Incident id={self.id} asset_id={self.asset_id} status='{self.status.value}'>"

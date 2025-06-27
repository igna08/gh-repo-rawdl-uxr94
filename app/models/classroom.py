from sqlalchemy import Column, ForeignKey, String, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class Classroom(Base):
    __tablename__ = "classrooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    code = Column(String, nullable=False)
    name = Column(Text, nullable=False)
    capacity = Column(Integer, nullable=True)
    responsible = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    school = relationship("School", back_populates="classrooms")
    assets = relationship("Asset", back_populates="classroom", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('school_id', 'code', name='uq_classroom_school_code'),
    )
    
    def __repr__(self):
        return f"Classroom(id={self.id}, name='{self.name}', code='{self.code}')"
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.core.database import Base

class School(Base):
    __tablename__ = "schools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    classrooms = relationship("Classroom", back_populates="school", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="school")
    subscriptions = relationship("Subscription", back_populates="school")
    
    def __repr__(self):
        return f"School(id={self.id}, name='{self.name}')"
    
from app.models.user_role import UserRole  # Add this at the end
from app.models.classroom import Classroom  # Add this at the end
from app.models.subscription import Subscription  # Add this at the end
from sqlalchemy import Column, ForeignKey, DateTime, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
# For relationship type hinting if needed in the future, not strictly required for string-based relationships
# from app.models.user import User 
# from app.models.role import Role
# from app.models.school import School

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(SmallInteger, ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), primary_key=True)
    
    assigned_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP", nullable=False)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role") # Assuming Role might have a 'user_roles' collection backref later
    school = relationship("School") # Assuming School might have a 'user_roles' collection backref later

    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}', school_id='{self.school_id}')>"

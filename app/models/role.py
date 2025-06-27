from sqlalchemy import Column, SmallInteger, String, Text # Added Text
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(SmallInteger, primary_key=True)
    name = Column(Text, nullable=False, unique=True) # Changed String to Text
    
    def __repr__(self):
        return f"Role(id={self.id}, name='{self.name}')"

# Valores predefinidos para los roles
from enum import Enum

class RoleEnum(str, Enum):
    SUPER_ADMIN = "Super Admin"
    SCHOOL_ADMIN = "School Admin"
    TEACHER = "Teacher"
    INVENTORY_MANAGER = "Inventory Manager"
    
    @classmethod
    def get_name(cls, role_id: int) -> str:
        role_names = {
            cls.SUPER_ADMIN: "Super Admin",
            cls.SCHOOL_ADMIN: "School Admin",
            cls.TEACHER: "Teacher",
            cls.INVENTORY_MANAGER: "Inventory Manager"
        }
        return role_names.get(role_id, "Unknown")
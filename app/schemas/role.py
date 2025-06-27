from sqlalchemy import Column, SmallInteger, String
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(SmallInteger, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    def __repr__(self):
        return f"Role(id={self.id}, name='{self.name}')"

# Valores predefinidos para los roles
class RoleEnum:
    SUPER_ADMIN = 1
    SCHOOL_ADMIN = 2
    TEACHER = 3
    INVENTORY_MANAGER = 4
    
    @classmethod
    def get_name(cls, role_id: int) -> str:
        role_names = {
            cls.SUPER_ADMIN: "Super Admin",
            cls.SCHOOL_ADMIN: "School Admin",
            cls.TEACHER: "Teacher",
            cls.INVENTORY_MANAGER: "Inventory Manager"
        }
        return role_names.get(role_id, "Unknown")
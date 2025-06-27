from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from uuid import UUID
from enum import Enum
from typing import Optional
from datetime import datetime

# --------------- Modelos existentes ---------------

class UserStatus(str, Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"

class UserRead(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

# --------------- Nuevos modelos para exponer roles ---------------

class RoleFlags(BaseModel):
    super_admin: bool
    school_admin: bool
    teacher: bool
    inventory_manager: bool

class UserWithRoles(UserRead):
    """
    Hereda todos los campos de UserRead y añade un bloque `roles`
    que indica, con booleanos, a qué roles pertenece el usuario.
    """
    roles: RoleFlags

    class Config:
        from_attributes = True

# ...existing code...
class User(Base):
    __tablename__ = "users"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    password_hash = Column(String, nullable=False)
    roles = relationship("UserRole", back_populates="user")
    deleted_at = Column(DateTime, nullable=True, default=None)

    def __repr__(self):
        return f"User(id={self.id}, email='{self.email}')"
# ...existing code...
    

#/////////////////////////// Sistema usuarios invitados ///////////////////////////

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"

class UserRoles(BaseModel):
    super_admin: bool = False
    school_admin: bool = False
    teacher: bool = False
    inventory_manager: bool = False

class UserRead(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    status: UserStatus
    created_at: datetime

    class Config:
        from_attributes = True

class UserWithRoles(UserRead):
    roles: UserRoles

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[UserStatus] = None

class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)

class ActionResponse(BaseModel):
    success: bool
    detail: str
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID, uuid4

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserRead(UserBase):
    id: UUID
    is_active: bool = True

    class Config:
        orm_mode = True

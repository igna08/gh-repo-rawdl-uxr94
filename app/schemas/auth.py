from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None # Changed from str to EmailStr for consistency

class UserInviteCreate(BaseModel):
    email: EmailStr
    role_id: UUID # Assuming role_id is UUID, can change to role_name: str if preferred
    school_id: Optional[UUID] = None

class UserInviteRead(BaseModel):
    id: UUID
    email: EmailStr
    role_id: UUID
    school_id: Optional[UUID]
    token: str # This is the invitation token, not JWT
    expires_at: datetime
    is_used: bool
    created_by_id: UUID

    class Config:
        orm_mode = True

class AcceptInviteSchema(BaseModel):
    token: str
    full_name: str
    password: str

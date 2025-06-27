from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class InvitationBase(BaseModel):
    email: EmailStr
    role_id: int
    school_id: UUID


class InvitationCreate(InvitationBase):
    pass


class InvitationRead(InvitationBase):
    id: UUID
    token: UUID
    expires_at: datetime
    used_at: Optional[datetime] = None
    sent_by: Optional[UUID] = None
    created_at: datetime
    is_valid: bool  # This will be a property on the ORM model

    class Config:
        from_attributes = True


class RegisterUserWithInvitation(BaseModel):
    full_name: str
    password: str
    invitation_token: UUID

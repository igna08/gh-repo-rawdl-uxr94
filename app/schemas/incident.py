from uuid import UUID
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, HttpUrl

# Enum for Incident Status - this can also be defined in models if preferred for DB consistency
# For Pydantic, string literals are often fine.
# class IncidentStatusEnum(str, Enum):
#     open = "open"
#     in_progress = "in_progress"
#     resolved = "resolved"
#     closed = "closed"

class IncidentBase(BaseModel):
    description: str
    photo_url: Optional[HttpUrl] = None

class IncidentCreate(IncidentBase):
    asset_id: UUID
    # reported_by_id will be injected by the service/router from current_user

class IncidentUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None # Should match values from IncidentStatusEnum in models
    photo_url: Optional[HttpUrl] = None

class IncidentRead(IncidentBase):
    id: UUID
    asset_id: UUID
    status: str # Should match values from IncidentStatusEnum in models
    reported_by: UUID
    reported_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Cambia orm_mode por from_attributes
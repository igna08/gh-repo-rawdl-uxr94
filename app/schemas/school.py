from uuid import UUID
from typing import Optional

from pydantic import BaseModel, HttpUrl

# Shared properties
class SchoolBase(BaseModel):
    name: str
    address: str
    description: Optional[str] = None
    logo_url: Optional[str] = None

# Properties to receive on school creation
class SchoolCreate(SchoolBase):
    pass

# Properties to receive on school update
class SchoolUpdate(SchoolBase):
    pass

# Properties to return to client
class SchoolRead(SchoolBase):
    id: UUID

    class Config:
        from_attributes = True  # Cambia orm_mode por from_attributes
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

# Shared properties
class ClassroomBase(BaseModel):
    name: str
    capacity: Optional[int] = None

# Properties to receive on classroom creation
class ClassroomCreate(ClassroomBase):
    pass

# Properties to receive on classroom update
class ClassroomUpdate(ClassroomBase):
    pass

# Properties to return to client
class ClassroomRead(ClassroomBase):
    id: UUID
    school_id: UUID

    class Config:
        from_attributes = True  # Cambia orm_mode por from_attributes
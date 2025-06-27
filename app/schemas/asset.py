from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from pydantic import BaseModel, HttpUrl
import uuid

# --- SHALLOW SCHEMAS PARA EVITAR RECURSIÓN ---

class AssetTemplateShallowRead(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        orm_mode = True

class AssetCategoryShallowRead(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
     from_attributes = True
# --- AssetCategory Schemas ---
class AssetCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class AssetCategoryCreate(BaseModel):
    name: str
    description: str

class AssetCategoryRead(AssetCategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    templates: List[AssetTemplateShallowRead] = []

    class Config:
        from_attributes = True
# --- AssetTemplate Schemas ---
class AssetTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    category_id: Optional[uuid.UUID] = None

class AssetTemplateCreate(AssetTemplateBase):
    pass

class AssetTemplateRead(AssetTemplateBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    category: Optional[AssetCategoryShallowRead] = None

    class Config:
        from_attributes = True  # Cambia orm_mode por from_attributes
# --- AssetEvent Schemas ---
class AssetEventBase(BaseModel):
    event_type: str
    metadata: Optional[Dict[str, Any]] = None

class AssetEventCreate(AssetEventBase):
    asset_id: UUID
    user_id: UUID

class AssetEventRead(AssetEventBase):
    id: UUID
    asset_id: UUID
    user_id: Optional[UUID]
    timestamp: datetime

    class Config:
        orm_mode = True

# --- Asset Schemas ---
class AssetBase(BaseModel):
    template_id: Optional[uuid.UUID] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    value_estimate: Optional[float] = None
    image_url: Optional[str] = None
    status: Optional[str] = "available"

class AssetCreate(AssetBase):
    classroom_id: UUID

class AssetUpdate(AssetBase):
    classroom_id: Optional[UUID] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    value_estimate: Optional[float] = None
    image_url: Optional[HttpUrl] = None
    status: Optional[str] = None

class AssetRead(AssetBase):
    id: UUID
    classroom_id: UUID
    created_at: datetime
    updated_at: datetime
    template: Optional[AssetTemplateRead] = None
    qr_code: Optional["QRCodeRead"] = None

    class Config:
        from_attributes = True  # Cambia orm_mode por from_attributes
# Import at the bottom to avoid circular import issues with QRCodeRead
from .qr import QRCodeRead  # noqa: E402

# Update forward references
AssetCategoryRead.update_forward_refs()
AssetTemplateRead.update_forward_refs()
AssetRead.update_forward_refs()
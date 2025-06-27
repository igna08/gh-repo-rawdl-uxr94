# app/models/invitation.py
from sqlalchemy import Column, ForeignKey, DateTime, Text, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

from app.core.database import Base


def _to_utc_aware(dt: datetime) -> datetime:
    """Devuelve un datetime con tzinfo=UTC, adaptándolo si era naive o si tenía otra zona."""
    if dt.tzinfo is None:
        # Asumir que un naive viene en UTC
        return dt.replace(tzinfo=timezone.utc)
    # Convertir cualquier zona a UTC
    return dt.astimezone(timezone.utc)


class Invitation(Base):
    __tablename__ = "invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, nullable=False)
    role_id = Column(SmallInteger, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    token = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    sent_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default="CURRENT_TIMESTAMP")
    
    def __repr__(self):
        return f"Invitation(id={self.id}, email='{self.email}', role_id={self.role_id})"
    
    @property
    def is_expired(self) -> bool:
        expires = _to_utc_aware(self.expires_at)
        now = datetime.now(timezone.utc)
        return expires < now
    
    @property
    def is_used(self) -> bool:
        return self.used_at is not None
    
    @property
    def is_valid(self) -> bool:
        expires = _to_utc_aware(self.expires_at)
        now = datetime.now(timezone.utc)
        return (self.used_at is None) and (expires > now)

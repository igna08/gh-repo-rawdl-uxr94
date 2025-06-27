from sqlalchemy import Column, String, DateTime, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import enum
import uuid
from datetime import datetime

Base = declarative_base()

class UserStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    status = Column(SqlEnum(UserStatus), default=UserStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

#//////////////////////////////////////////// Sistema usuarios invitados /////////////////////////////////////////////
    
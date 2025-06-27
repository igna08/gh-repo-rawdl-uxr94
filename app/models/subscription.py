import enum
from sqlalchemy import Column, ForeignKey, String, DateTime, Date, Enum as SQLAlchemyEnum, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, date

from app.core.database import Base
# from app.models.school import School # For relationship, handled by string reference

# --- Plan Model ---
class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False)
    duration_days = Column(Integer, nullable=False) # e.g., 30 for monthly, 365 for yearly
    features_list = Column(ARRAY(String), default=[])
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<Plan id={self.id} name='{self.name}'>"

# --- Subscription Enums and Model ---
class SubscriptionStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive" # e.g. created but not paid, or explicitly deactivated
    past_due = "past_due"
    canceled = "canceled"
    expired = "expired" # Added for clarity when end_date is passed

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLAlchemyEnum(SubscriptionStatusEnum, name="subscription_status_enum"), nullable=False, default=SubscriptionStatusEnum.inactive)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow)

    school = relationship("School", back_populates="subscriptions") # In School model: subscriptions = relationship("Subscription", back_populates="school")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subscription id={self.id} school_id={self.school_id} plan_id={self.plan_id} status='{self.status.value}'>"


# --- Payment Enums and Model ---
class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded" # Added for completeness

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    gateway_payment_id = Column(String, nullable=True, index=True) # e.g., Stripe charge ID
    status = Column(SQLAlchemyEnum(PaymentStatusEnum, name="payment_status_enum"), nullable=False, default=PaymentStatusEnum.pending)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self):
        return f"<Payment id={self.id} subscription_id={self.subscription_id} amount={self.amount} status='{self.status.value}'>"

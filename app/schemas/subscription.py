from uuid import UUID
from typing import Optional, List
from datetime import datetime, date

from pydantic import BaseModel

# --- Plan Schemas ---
class PlanBase(BaseModel):
    name: str
    price: float
    duration_days: int # e.g., 30 for monthly, 365 for yearly
    features_list: List[str] = []
    description: Optional[str] = None

class PlanCreate(PlanBase):
    pass

class PlanUpdate(BaseModel): # All fields optional for update
    name: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    features_list: Optional[List[str]] = None
    description: Optional[str] = None

class PlanRead(PlanBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --- Subscription Schemas ---
class SubscriptionBase(BaseModel):
    school_id: UUID # School is the subscribing entity
    plan_id: UUID

class SubscriptionCreate(SubscriptionBase):
    # start_date, end_date, status are set by the service
    pass

class SubscriptionRead(SubscriptionBase):
    id: UUID
    start_date: date
    end_date: date
    status: str # Should match SubscriptionStatusEnum values
    plan: PlanRead # Include plan details
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# --- Payment Schemas ---
class PaymentBase(BaseModel):
    subscription_id: UUID
    amount: float
    gateway_payment_id: Optional[str] = None # ID from payment gateway like Stripe, PayPal
    status: str # Should match PaymentStatusEnum values

class PaymentCreate(PaymentBase):
    # payment_date is set by the service upon creation
    pass

class PaymentRead(PaymentBase):
    id: UUID
    payment_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

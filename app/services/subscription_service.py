from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.subscription import Plan, Subscription, Payment, SubscriptionStatusEnum, PaymentStatusEnum
from app.schemas.subscription import PlanCreate, PlanUpdate, SubscriptionCreate, PaymentCreate
from app.models.school import School # For type hinting and checks
# from app.services.school_service import get_school # If needed for validation

# --- Plan Management ---
def create_plan(db: Session, plan_in: PlanCreate) -> Plan:
    db_plan = Plan(**plan_in.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_plan(db: Session, plan_id: UUID) -> Plan | None:
    return db.query(Plan).filter(Plan.id == plan_id).first()

def get_plans(db: Session, skip: int = 0, limit: int = 100) -> List[Plan]:
    return db.query(Plan).offset(skip).limit(limit).all()

def update_plan(db: Session, plan_id: UUID, plan_in: PlanUpdate) -> Plan | None:
    db_plan = get_plan(db, plan_id)
    if not db_plan:
        return None
    
    update_data = plan_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plan, key, value)
    
    db_plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_plan)
    return db_plan

def delete_plan(db: Session, plan_id: UUID) -> Plan | None:
    # Consider implications: what if subscriptions are active on this plan?
    # Soft delete or preventing deletion if active subscriptions exist might be better.
    # For now, hard delete as per typical CRUD.
    db_plan = get_plan(db, plan_id)
    if not db_plan:
        return None
    
    # Check for active subscriptions (optional, depends on business logic)
    active_subscriptions = db.query(Subscription).filter(
        Subscription.plan_id == plan_id,
        Subscription.status.in_([SubscriptionStatusEnum.active, SubscriptionStatusEnum.past_due])
    ).count()
    if active_subscriptions > 0:
        raise ValueError(f"Cannot delete plan {plan_id} as it has active subscriptions.")

    db.delete(db_plan)
    db.commit()
    return db_plan


# --- Subscription Management ---
def create_subscription(db: Session, sub_in: SubscriptionCreate) -> Subscription | None:
    # Validate school
    db_school = db.query(School).filter(School.id == sub_in.school_id, School.deleted_at == None).first()
    if not db_school:
        raise ValueError(f"School with id {sub_in.school_id} not found.")

    # Validate plan
    db_plan = get_plan(db, sub_in.plan_id)
    if not db_plan:
        raise ValueError(f"Plan with id {sub_in.plan_id} not found.")

    # Check for existing active/inactive/past_due subscription for this school and plan
    existing_sub = db.query(Subscription).filter(
        Subscription.school_id == sub_in.school_id,
        Subscription.plan_id == sub_in.plan_id,
        Subscription.status.in_([
            SubscriptionStatusEnum.active, 
            SubscriptionStatusEnum.inactive, 
            SubscriptionStatusEnum.past_due
        ])
    ).first()

    if existing_sub:
        # If an inactive subscription exists, it might be reactivated by payment.
        # If active/past_due, prevent creating a duplicate.
        if existing_sub.status == SubscriptionStatusEnum.inactive:
            # Could return this for payment, or update its dates if needed
            # For now, let's assume a new payment will target this inactive subscription
            return existing_sub 
        else:
            raise ValueError(f"School {sub_in.school_id} already has an active or past_due subscription for plan {sub_in.plan_id}.")


    start_date = date.today()
    end_date = start_date + timedelta(days=db_plan.duration_days)
    
    db_subscription = Subscription(
        school_id=sub_in.school_id,
        plan_id=sub_in.plan_id,
        start_date=start_date,
        end_date=end_date,
        status=SubscriptionStatusEnum.inactive # Initial status, becomes active upon payment
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

def get_subscription(db: Session, sub_id: UUID) -> Subscription | None:
    return db.query(Subscription).filter(Subscription.id == sub_id).first()

def get_subscriptions_by_school(db: Session, school_id: UUID, skip: int = 0, limit: int = 100) -> List[Subscription]:
    return db.query(Subscription).filter(Subscription.school_id == school_id).order_by(Subscription.start_date.desc()).offset(skip).limit(limit).all()

def get_active_subscription_for_school(db: Session, school_id: UUID) -> Subscription | None:
    """Gets the current active or past_due subscription for a school."""
    return db.query(Subscription).filter(
        Subscription.school_id == school_id,
        Subscription.status.in_([SubscriptionStatusEnum.active, SubscriptionStatusEnum.past_due])
    ).order_by(Subscription.end_date.desc()).first()


def update_subscription_status(db: Session, sub_id: UUID, status: SubscriptionStatusEnum) -> Subscription | None:
    db_sub = get_subscription(db, sub_id)
    if not db_sub:
        return None
    
    db_sub.status = status
    db_sub.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_sub)
    return db_sub

def renew_subscription(db: Session, sub_id: UUID, new_start_date: Optional[date] = None) -> Subscription | None:
    db_sub = get_subscription(db, sub_id)
    if not db_sub or not db_sub.plan:
        return None # Or raise error

    # Determine the new start date for the renewal period
    # If not provided, and current period has ended, start from today.
    # If current period is active, start from current end_date + 1 day.
    start_date_for_renewal = new_start_date
    if start_date_for_renewal is None:
        if db_sub.end_date < date.today(): # Expired or past
            start_date_for_renewal = date.today()
        else: # Still active, renew from end date
            start_date_for_renewal = db_sub.end_date + timedelta(days=1)
    
    db_sub.start_date = start_date_for_renewal
    db_sub.end_date = start_date_for_renewal + timedelta(days=db_sub.plan.duration_days)
    db_sub.status = SubscriptionStatusEnum.active # Mark as active upon renewal
    db_sub.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_sub)
    return db_sub

# --- Payment Processing ---
def record_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    # Validate subscription
    db_sub = get_subscription(db, payment_in.subscription_id)
    if not db_sub:
        raise ValueError(f"Subscription with id {payment_in.subscription_id} not found.")

    db_payment = Payment(**payment_in.model_dump())
    db_payment.payment_date = datetime.utcnow() # Set payment date
    
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def handle_successful_payment_webhook(
    db: Session, 
    gateway_payment_id: str, 
    amount_received: float, 
    subscription_id: UUID # Assuming webhook provides the subscription ID directly or indirectly
) -> Subscription | None:
    
    db_sub = get_subscription(db, subscription_id)
    if not db_sub:
        # Log this: payment received for non-existent/unknown subscription
        print(f"Webhook Error: Subscription {subscription_id} not found for payment {gateway_payment_id}")
        return None
    
    # Validate amount if possible (e.g., against plan price)
    if db_sub.plan and db_sub.plan.price != amount_received:
        # Log this discrepancy, may need manual review
        print(f"Webhook Warning: Payment amount {amount_received} for sub {subscription_id} "
              f"does not match plan price {db_sub.plan.price}.")
        # Proceeding anyway for this simplified version

    # Record the payment
    payment_data = PaymentCreate(
        subscription_id=db_sub.id,
        amount=amount_received,
        gateway_payment_id=gateway_payment_id,
        status=PaymentStatusEnum.succeeded # Set by webhook logic
    )
    record_payment(db, payment_data)

    # Update subscription: activate and renew/extend
    # Determine if this is initial activation or renewal
    if db_sub.status == SubscriptionStatusEnum.inactive:
        # Initial activation. Set start_date to today if it's in the past or not set properly.
        # The create_subscription already sets start/end dates. Here we just activate.
        db_sub.status = SubscriptionStatusEnum.active
        db_sub.start_date = date.today() # Ensure start date is current for new activations
        db_sub.end_date = date.today() + timedelta(days=db_sub.plan.duration_days)
        db_sub.updated_at = datetime.utcnow()
    else:
        # Renewal for an existing (possibly active, past_due, or even expired) subscription
        renewed_sub = renew_subscription(db, db_sub.id) # renew_subscription handles date logic and sets status to active
        if not renewed_sub: # Should not happen if db_sub exists
             print(f"Webhook Error: Failed to renew subscription {db_sub.id}")
             return None
        db_sub = renewed_sub # get the updated object

    db.commit()
    db.refresh(db_sub)
    return db_sub

# --- Cron/Scheduled Tasks (Conceptual) ---
# - Check for subscriptions nearing expiration and send reminder emails.
# - Check for subscriptions that are past_due and attempt to re-charge or notify.
# - Update status of expired subscriptions to 'expired'.
# These would typically be run by a separate scheduler (e.g., Celery Beat, APScheduler).
def check_and_update_subscription_statuses(db: Session):
    """Conceptual: Updates statuses of expired or past-due subscriptions."""
    today = date.today()
    
    # Mark active/past_due subscriptions as expired if end_date has passed
    expired_subs = db.query(Subscription).filter(
        Subscription.end_date < today,
        Subscription.status.in_([SubscriptionStatusEnum.active, SubscriptionStatusEnum.past_due])
    ).all()
    for sub in expired_subs:
        sub.status = SubscriptionStatusEnum.expired
        sub.updated_at = datetime.utcnow()
    
    # Potentially handle past_due logic (e.g., if payment failed N days ago)
    # ...
    
    db.commit()
    # print(f"Updated status for {len(expired_subs)} subscriptions to 'expired'.")
    return len(expired_subs)

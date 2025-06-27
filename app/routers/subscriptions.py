import json
from uuid import UUID
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.subscription import (
    PlanCreate, PlanRead, PlanUpdate,
    SubscriptionCreate, SubscriptionRead,
    PaymentCreate, PaymentRead # Payment schemas might be used if direct payment recording is exposed
)
from app.services import subscription_service, school_service # school_service for school validation
from app.models.subscription import Plan as PlanModel, Subscription as SubscriptionModel # For response_model

# Placeholder for current_user_id dependency (e.g. for admin-only actions)
async def get_current_admin_user() -> UUID: # Simulate an admin user
    return UUID("97f45c67-5c74-493d-bcb6-757c5253d0a1") # Dummy User ID

router = APIRouter(
    tags=["subscriptions"],
    responses={404: {"description": "Not found"}},
)

# --- Plans Routes ---
@router.post(
    "/plans/", 
    response_model=PlanRead, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subscription plan (Admin)"
)
def create_new_plan(
    plan_in: PlanCreate,
    db: Session = Depends(get_db),
    # current_admin: UUID = Depends(get_current_admin_user) # Uncomment if admin auth is set up
):
    # Check for existing plan by name to avoid duplicates if name should be unique
    # existing_plan = db.query(PlanModel).filter(PlanModel.name == plan_in.name).first()
    # if existing_plan:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan with this name already exists.")
    try:
        return subscription_service.create_plan(db=db, plan_in=plan_in)
    except Exception as e: # Generic error for now
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/plans/", 
    response_model=List[PlanRead],
    summary="Get all subscription plans"
)
def read_all_plans(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return subscription_service.get_plans(db, skip=skip, limit=limit)

@router.get(
    "/plans/{plan_id}", 
    response_model=PlanRead,
    summary="Get a specific subscription plan by ID"
)
def read_single_plan(
    plan_id: UUID = Path(..., description="The ID of the plan to retrieve"),
    db: Session = Depends(get_db)
):
    db_plan = subscription_service.get_plan(db, plan_id=plan_id)
    if db_plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return db_plan

@router.put(
    "/plans/{plan_id}", 
    response_model=PlanRead,
    summary="Update a subscription plan (Admin)"
)
def update_existing_plan(
    plan_id: UUID = Path(..., description="The ID of the plan to update"),
    plan_in: PlanUpdate = Body(...),
    db: Session = Depends(get_db),
    # current_admin: UUID = Depends(get_current_admin_user) # Uncomment if admin auth
):
    updated_plan = subscription_service.update_plan(db, plan_id=plan_id, plan_in=plan_in)
    if updated_plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found or update failed")
    return updated_plan

@router.delete(
    "/plans/{plan_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a subscription plan (Admin)"
)
def delete_single_plan(
    plan_id: UUID = Path(..., description="The ID of the plan to delete"),
    db: Session = Depends(get_db),
    # current_admin: UUID = Depends(get_current_admin_user) # Uncomment if admin auth
):
    try:
        deleted_plan = subscription_service.delete_plan(db, plan_id=plan_id)
    except ValueError as e: # Catch specific errors from service (e.g., plan has active subs)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    if deleted_plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return None

# --- Subscriptions Routes ---
@router.post(
    "/subscriptions/", 
    response_model=SubscriptionRead, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subscription for a school"
)
def create_new_subscription(
    sub_in: SubscriptionCreate, # Contains school_id and plan_id
    db: Session = Depends(get_db),
    # current_admin: Optional[UUID] = Depends(get_current_admin_user) # Or other authorized user
):
    # School and Plan validation is done in the service layer
    try:
        created_sub = subscription_service.create_subscription(db=db, sub_in=sub_in)
    except ValueError as e: # Catch specific errors from service layer
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if created_sub is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription could not be created.")
    return created_sub

@router.get(
    "/subscriptions/{subscription_id}", 
    response_model=SubscriptionRead,
    summary="Get a specific subscription by its ID"
)
def read_single_subscription(
    subscription_id: UUID = Path(..., description="The ID of the subscription to retrieve"),
    db: Session = Depends(get_db)
):
    db_sub = subscription_service.get_subscription(db, sub_id=subscription_id)
    if db_sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return db_sub

@router.get(
    "/schools/{school_id}/subscription", 
    response_model=SubscriptionRead, # Assuming one active/primary subscription per school for simplicity
    summary="Get current active/past_due subscription for a school"
)
def get_school_active_subscription(
    school_id: UUID = Path(..., description="The ID of the school"),
    db: Session = Depends(get_db)
):
    # Validate school exists
    db_school = school_service.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with id {school_id} not found.")

    active_sub = subscription_service.get_active_subscription_for_school(db, school_id=school_id)
    if active_sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active or past_due subscription found for this school.")
    return active_sub
    
@router.get(
    "/schools/{school_id}/subscriptions",
    response_model=List[SubscriptionRead],
    summary="Get all subscriptions for a school (history)"
)
def get_school_all_subscriptions(
    school_id: UUID = Path(..., description="The ID of the school"),
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db)
):
    db_school = school_service.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with id {school_id} not found.")
    
    subscriptions = subscription_service.get_subscriptions_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return subscriptions


@router.post(
    "/subscriptions/{subscription_id}/renew", 
    response_model=SubscriptionRead,
    summary="Manually renew a subscription (Admin or System)"
)
def manually_renew_subscription(
    subscription_id: UUID = Path(..., description="The ID of the subscription to renew"),
    db: Session = Depends(get_db),
    # current_admin: UUID = Depends(get_current_admin_user) # If admin action
):
    renewed_sub = subscription_service.renew_subscription(db, sub_id=subscription_id)
    if renewed_sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found or renewal failed.")
    return renewed_sub

# --- Webhooks Route ---
@router.post(
    "/webhooks/payments",
    status_code=status.HTTP_200_OK, # Webhooks usually expect a 2xx response quickly
    summary="Handle payment gateway webhooks (e.g., Stripe)"
)
async def handle_payment_webhook(
    request: Request, # Raw request to access body
    db: Session = Depends(get_db)
):
    payload_bytes = await request.body()
    # For now, assuming payload is JSON and contains expected fields.
    # Real-world: Verify signature (e.g., Stripe-Signature header)
    # Real-world: More robust parsing and error handling.
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.")

    # This is a simplified example. Stripe's actual webhook payload is more complex.
    # We expect 'type' (e.g. 'payment_intent.succeeded'), 'data.object.id' (gateway_payment_id),
    # 'data.object.amount_received', and 'data.object.metadata.subscription_id'.
    event_type = payload.get("type")
    data_object = payload.get("data", {}).get("object", {})

    if event_type == "payment_intent.succeeded": # Example event type
        gateway_payment_id = data_object.get("id")
        amount_received_cents = data_object.get("amount_received") # Stripe amounts are in cents
        event_metadata = data_object.get("metadata", {})
        subscription_id_str = event_metadata.get("subscription_id") # Assuming we set this in metadata when creating payment intent

        if not all([gateway_payment_id, amount_received_cents is not None, subscription_id_str]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields in webhook payload.")

        try:
            subscription_id = UUID(subscription_id_str)
            amount_received_main_unit = float(amount_received_cents) / 100.0 # Convert cents to main unit
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subscription_id or amount format.")

        updated_subscription = subscription_service.handle_successful_payment_webhook(
            db=db,
            gateway_payment_id=gateway_payment_id,
            amount_received=amount_received_main_unit,
            subscription_id=subscription_id 
        )
        if updated_subscription is None:
            # Service might return None if sub not found or other issue. Logged in service.
            # For webhook, still return 200 to acknowledge receipt, unless it's a critical error we can't recover from.
            # Or choose a different status code if appropriate.
            print(f"Webhook for {gateway_payment_id}: handle_successful_payment_webhook returned None.")
            # Consider raising HTTPException if the webhook indicates a permanent failure for this payment
            # that the gateway shouldn't retry. For now, generic success.
            return {"status": "webhook received, processing issue logged"}

        return {"status": "webhook processed successfully", "subscription_id": updated_subscription.id}
    
    # Handle other event types if necessary
    # e.g., payment_intent.payment_failed -> update_subscription_status to past_due or inactive

    return {"status": "webhook received, event not handled"}

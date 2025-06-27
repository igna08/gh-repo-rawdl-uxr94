from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.models.user import UserCreate, UserRead, UserUpdate
from app.services.user_service import user_service
# This dependency will be created later
# from dependencies import get_db 

router = APIRouter(
    prefix="/users",
    tags=["users"],
    # dependencies=[Depends(get_db)], # Add this back when get_db is defined
    responses={404: {"description": "Not found"}},
)

# Placeholder for get_db dependency
def get_db():
    # This should yield a SQLAlchemy Session
    # For now, returning None as a placeholder
    print("get_db called - placeholder")
    yield None 

@router.post("/", response_model=UserRead, status_code=201)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # db_user = user_service.get_user_by_email(db, email=user_in.email)
    # if db_user:
    #     raise HTTPException(status_code=400, detail="Email already registered")
    # return user_service.create_user(db=db, user_in=user_in)
    print(f"Creating user: {user_in.email}") # Placeholder
    # This is a placeholder response, actual implementation will use user_service
    return UserRead(id=UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"), email=user_in.email, full_name=user_in.full_name, is_active=True)


@router.get("/", response_model=List[UserRead])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # users = user_service.get_users(db, skip=skip, limit=limit)
    # return users
    print(f"Reading users with skip: {skip}, limit: {limit}") # Placeholder
    return [] # Placeholder

@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: UUID, db: Session = Depends(get_db)):
    # db_user = user_service.get_user(db, user_id=user_id)
    # if db_user is None:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return db_user
    print(f"Reading user: {user_id}") # Placeholder
    # This is a placeholder response
    return UserRead(id=user_id, email="user@example.com", full_name="John Doe", is_active=True)


@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, user_in: UserUpdate, db: Session = Depends(get_db)):
    # db_user = user_service.update_user(db, user_id=user_id, user_in=user_in)
    # if db_user is None:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return db_user
    print(f"Updating user: {user_id}") # Placeholder
    # This is a placeholder response
    return UserRead(id=user_id, email=user_in.email or "user@example.com", full_name=user_in.full_name or "John Doe", is_active=True)


@router.delete("/{user_id}", response_model=UserRead) # Should ideally be 204 No Content or the deleted object
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    # db_user = user_service.delete_user(db, user_id=user_id)
    # if db_user is None:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return db_user
    print(f"Deleting user: {user_id}") # Placeholder
    # This is a placeholder response
    return UserRead(id=user_id, email="deleted@example.com", full_name="Deleted User", is_active=False)

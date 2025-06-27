from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta # Added for token expiry

from app.core.database import get_db
from app.models.user import UserCreate, UserRead, Token # UserCreate, UserRead are Pydantic models from app.models.user
from app.schemas.invitation import RegisterUserWithInvitation # Pydantic schema for the new endpoint
import app.services.auth_service as auth_service
import app.services.invitation_service as invitation_service # Added
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    NOTE: This endpoint is for open registration which might be disabled or restricted.
    Primary registration flow is via `/register/invitation`.
    """
    # The auth_service.register_user function already handles
    # HTTPException for existing email.
    # This will create a user with 'pending' status and no roles.
    db_user = auth_service.register_user(db=db, user_in=user_in)
    return db_user


@router.post("/register/invitation", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_with_invitation(
    payload: RegisterUserWithInvitation, 
    db: Session = Depends(get_db)
) -> UserRead:
    """
    Register a new user using an invitation token.
    """
    invitation = invitation_service.get_invitation_by_token(db=db, token=payload.invitation_token)

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation token not found."
        )

    if not invitation.is_valid: # Checks used_at and expires_at via the ORM property
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token."
        )

    # Prepare UserCreate Pydantic model using email from invitation
    user_to_create = UserCreate(
        full_name=payload.full_name,
        email=invitation.email,  # Email from invitation, not payload
        password=payload.password
    )

    try:
        # Register the user with the invitation details
        new_user = auth_service.register_user_with_invitation(
            db=db,
            user_in=user_to_create,
            invitation=invitation
        )

        # Mark the invitation as used
        invitation_service.mark_invitation_as_used(db=db, token=payload.invitation_token)
        
        # UserRead schema will handle the response model mapping
        return new_user
    except HTTPException as e:
        # Re-raise HTTPExceptions from the service layer (e.g., email mismatch, user already active)
        raise e
    except Exception as e:
        import traceback
        print("Error in register_with_invitation:", e)
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration with invitation."
        )


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login for existing user to get an access token.
    """
    user = auth_service.authenticate_user(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, # Using email as subject, consistent with get_current_user
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

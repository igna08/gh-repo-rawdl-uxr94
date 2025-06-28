from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import uuid

from app.core.database import get_db
from app.models.user import UserCreate, UserRead, Token, User , GoogleLoginRequest # Agregado User (el modelo de SQLAlchemy)
from app.schemas.invitation import RegisterUserWithInvitation
import app.services.auth_service as auth_service
import app.services.invitation_service as invitation_service
from app.core.security import create_access_token, get_password_hash  # Agregado get_password_hash
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Modelo Pydantic para Google Login Request


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

@router.post("/google-login", response_model=Token)
async def google_login(
    payload: GoogleLoginRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Login or register user with Google OAuth2.
    """
    # 1. Validar el id_token con Google
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de Google inválido",
        )

    # 2. Extraer datos
    email = idinfo.get("email")
    sub = idinfo.get("sub")
    name = idinfo.get("name", email.split("@")[0] if email else "")

    if not email or not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Respuesta de Google incompleta",
        )

    # 3. Buscar o crear usuario - CORREGIDO: usar el modelo User de SQLAlchemy
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Registro automático
        user = User(
            full_name=name,
            email=email,
            status="active",  # Usuario OAuth se activa automáticamente
            password_hash=get_password_hash(uuid.uuid4().hex),
            # Nota: Si tienes campos oauth_provider y oauth_id en tu modelo User, descomenta estas líneas:
            # oauth_provider="google",
            # oauth_id=sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Si ya existe, asegurar que esté activo
        if user.status == "pending":
            user.status = "active"
            db.commit()
        
        # Si tienes campos OAuth en tu modelo User, descomenta estas líneas:
        # if not user.oauth_provider:
        #     user.oauth_provider = "google"
        #     user.oauth_id = sub
        #     db.commit()

    # 4. Generar access token (mismo método que en /login)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email,
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

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

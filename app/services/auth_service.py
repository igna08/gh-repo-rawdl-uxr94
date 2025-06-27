from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from jose import JWTError

from app.models.user import User, UserCreate # Adjusted to import ORM User from app.models.user
from app.models.invitation import Invitation # Added
from app.models.user_role import UserRole # Added
from app.core.security import get_password_hash, verify_password, decode_token
from app.core.config import settings
from app.core.database import get_db

def register_user(db: Session, user_in: UserCreate) -> User:
    """
    Registers a new user in the database.
    - Checks if a user with the given email already exists.
    - Hashes the provided password.
    - Creates a new User instance and saves it to the database.
    """
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(user_in.password)

    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_password,
        status='pending' # Explicitly setting to 'pending', no roles assigned here
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def register_user_with_invitation(db: Session, user_in: UserCreate, invitation: Invitation) -> User:
    """
    Registers a new user using an invitation.
    - Validates email against invitation.
    - Checks for existing active/suspended users.
    - Hashes password.
    - Creates User with 'active' status.
    - Creates UserRole based on invitation.
    """
    if user_in.email != invitation.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration email does not match invitation email.",
        )

    # Check for existing user who is active or suspended
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user and (existing_user.status == 'active' or existing_user.status == 'suspended'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists and is active/suspended.",
        )
    # If user exists and is 'pending', this new registration will effectively override it by creating a new one,
    # or ideally, we'd update the pending user. For now, creating a new one if no active/suspended one exists.
    # If an email exists with 'pending', the original register_user would fail.
    # This function assumes that an invitation allows creating a new, active user,
    # potentially leaving a 'pending' one orphaned if not handled by a cleanup process.
    # Or, the check in register_user (called before this usually in the flow) would prevent it.
    # Given this function is separate, it needs its own check.

    hashed_password = get_password_hash(user_in.password)

    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_password,
        status='active'  # Invited users are active by default
    )
    db.add(db_user)
    # We need the user ID for UserRole, so flush to get it.
    # Committing later ensures both User and UserRole are saved together.
    db.flush() 

    db_user_role = UserRole(
        user_id=db_user.id,
        role_id=invitation.role_id,
        school_id=invitation.school_id
    )
    db.add(db_user_role)

    db.commit()
    db.refresh(db_user)
    # To load the roles relationship if needed by the caller, though not explicitly required by UserRead:
    # from sqlalchemy.orm import selectinload
    # db.refresh(db_user, attribute_names=['roles']) # Example if 'roles' is a relationship on User model
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticates a user by email and password.
    - Retrieves the user by email.
    - Verifies the provided password against the stored hash.
    - Returns the user object if authentication is successful, otherwise None.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = TokenData(username=username) # Optional as per instructions
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == username).first() # Assuming 'sub' is email
    if user is None:
        raise credentials_exception
    return user

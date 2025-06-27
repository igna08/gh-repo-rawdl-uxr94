from datetime import datetime, timedelta
from typing import Any, Optional, Union
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from uuid import UUID
from app.core.config import settings

# Contexto para manejar hashes de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, UUID], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crea un token JWT con un subject (normalmente user_id) y un tiempo de expiración
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera un hash de contraseña
    """
    return pwd_context.hash(password)

def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica un token JWT y retorna su payload
    """
    return jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

def generate_invitation_token() -> str:
    """
    Genera un token de invitación (UUID aleatorio)
    """
    return str(uuid.uuid4())

def generate_password_reset_token(email: str) -> str:
    """
    Genera un token de restablecimiento de contraseña
    """
    delta = timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verifica un token de restablecimiento de contraseña
    """
    try:
        decoded_token = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded_token["sub"]
    except JWTError:
        return None
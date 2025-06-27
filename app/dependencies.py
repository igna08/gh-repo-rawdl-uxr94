from fastapi import Depends, HTTPException, logger, status
from fastapi import security
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Generator, Optional
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.user_role import UserRole
from app.services.user_service import get_user_by_email

# Configuración de OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")

# Roles del sistema
class Role:
    SUPER_ADMIN = 1
    SCHOOL_ADMIN = 2
    TEACHER = 3
    INVENTORY_MANAGER = 4

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Dependencia para obtener el usuario actual autenticado.
    Devuelve también si el usuario es SUPER_ADMIN según la lógica de roles.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=user_id)
    if user is None:
        raise credentials_exception

    # 3. Verificar que no esté eliminado
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deleted",
        )

    # 4. Verificar que esté activo
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User account is {user.status}",
        )

    # 5. Comprobar flags de cada rol (usando tu función check_user_role)
    is_super_admin       = check_user_role(db, user.id, Role.SUPER_ADMIN)
    is_school_admin      = check_user_role(db, user.id, Role.SCHOOL_ADMIN)
    is_teacher           = check_user_role(db, user.id, Role.TEACHER)
    is_inventory_manager = check_user_role(db, user.id, Role.INVENTORY_MANAGER)

    return {
        "user": user,
        "roles": {
            "super_admin": is_super_admin,
            "school_admin": is_school_admin,
            "teacher": is_teacher,
            "inventory_manager": is_inventory_manager
        }
    }

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Dependencia para verificar que el usuario está activo
    """
    if current_user["user"].status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user

# Función auxiliar para verificar si un usuario tiene un rol específico en una escuela
def check_user_role(db: Session, user_id: UUID, role_id: int, school_id: Optional[UUID] = None):
    """
    Verifica si un usuario tiene un rol específico en una escuela
    """
    from app.models.user_role import UserRole
    
    query = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id
    )
    
    if school_id:
        query = query.filter(UserRole.school_id == school_id)
    
    return query.first() is not None

# Dependencias de roles (ejemplos)
def get_super_admin(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Dependencia para verificar si el usuario es un SUPER_ADMIN
    """
    if not check_user_role(db, current_user["user"].id, Role.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

def get_school_admin(
    school_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Dependencia para verificar si el usuario es un SCHOOL_ADMIN de una escuela específica
    """
    # Los SUPER_ADMIN tienen acceso a todas las escuelas
    if check_user_role(db, current_user["user"].id, Role.SUPER_ADMIN):
        return current_user

    if not check_user_role(db, current_user["user"].id, Role.SCHOOL_ADMIN, school_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this school",
        )
    return current_user



async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifica que el usuario sea administrador (super_admin o school_admin)
    """
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            admin_roles = db.query(UserRole).join(Role).filter(
                UserRole.user_id == current_user.id,
                Role.name.in_(["super_admin", "school_admin"])
            ).first()
            
            if not admin_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Administrator privileges required."
                )
            
            return current_user
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying admin privileges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying permissions"
        )

def check_user_permission(required_role: str):
    """
    Dependencia para verificar permisos específicos
    """
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            
            try:
                user_role = db.query(UserRole).join(Role).filter(
                    UserRole.user_id == current_user.id,
                    Role.name == required_role
                ).first()
                
                if not user_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. {required_role} role required."
                    )
                
                return current_user
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking permission {required_role}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying permissions"
            )
    
    return permission_checker

# Dependencias específicas para diferentes roles
get_teacher = check_user_permission("teacher")
get_inventory_manager = check_user_permission("inventory_manager")
get_school_admin = check_user_permission("school_admin")
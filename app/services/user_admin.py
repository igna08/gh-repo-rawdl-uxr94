
# app/services/user_service.py
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.user_role import  UserRole
from app.models.role import Role
from app.models.user import UserWithRoles, UserUpdate, UserRoles, ActionResponse

logger = logging.getLogger(__name__)
def list_users(db, skip=0, limit=100):
    """
    Lista todos los usuarios no eliminados con sus roles
    """
    try:
        # Consulta usuarios no eliminados
        users_query = db.query(User).filter(
            User.deleted_at.is_(None)
        ).offset(skip).limit(limit)
        
        users = users_query.all()
        result = []
        
        for user in users:
            # Obtener roles del usuario
            user_roles = get_user_roles(db, user.id)
            
            user_with_roles = UserWithRoles(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                status=user.status,
                created_at=user.created_at,
                roles=user_roles
            )
            result.append(user_with_roles)
        
        logger.info(f"Listed {len(result)} users")
        return result
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

def get_user_by_id(db: Session, user_id: UUID) -> UserWithRoles:
    """
    Obtiene un usuario específico por ID con sus roles
    """
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Obtener roles del usuario
        user_roles = get_user_roles(db, user.id)
        
        return UserWithRoles(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            status=user.status,
            created_at=user.created_at,
            roles=user_roles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user"
        )

def update_user(db: Session, user_id: UUID, user_data: UserUpdate) -> UserWithRoles:
    """
    Actualiza los datos de un usuario
    """
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validar que el email no esté en uso por otro usuario
        if user_data.email and user_data.email != user.email:
            existing_user = db.query(User).filter(
                and_(
                    User.email == user_data.email,
                    User.id != user_id,
                    User.deleted_at.is_(None)
                )
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        # Actualizar campos
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        # Si se reactiva un usuario, resetear deleted_at
        if user_data.status == "active" and user.deleted_at:
            user.deleted_at = None
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated user {user_id}")
        
        # Retornar usuario con roles
        return get_user_by_id(db, user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

def block_user(db: Session, user_id: UUID) -> ActionResponse:
    """
    Bloquea un usuario (soft delete)
    """
    try:
        user = db.query(User).filter(
            and_(User.id == user_id, User.deleted_at.is_(None))
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # No permitir auto-bloqueo del superadmin
        # Esta validación se podría hacer en el endpoint si tienes acceso al usuario actual
        
        # Soft delete
        user.deleted_at = datetime.utcnow()
        user.status = "suspended"
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Blocked user {user_id}")
        
        return ActionResponse(
            success=True,
            detail=f"User {user.full_name} has been blocked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error blocking user {user_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error blocking user"
        )

def get_user_roles(db: Session, user_id: UUID) -> UserRoles:
    """
    Obtiene los roles de un usuario específico
    """
    try:
        # Consultar roles del usuario
        user_roles_query = db.query(UserRole).join(Role).filter(
            UserRole.user_id == user_id
        ).all()
        
        roles = UserRoles()
        
        for user_role in user_roles_query:
            role_name = user_role.role.name
            if role_name == "super_admin":
                roles.super_admin = True
            elif role_name == "school_admin":
                roles.school_admin = True
            elif role_name == "teacher":
                roles.teacher = True
            elif role_name == "inventory_manager":
                roles.inventory_manager = True
        
        return roles
        
    except Exception as e:
        logger.error(f"Error getting roles for user {user_id}: {str(e)}")
        return UserRoles()  # Retornar roles vacíos en caso de error

def search_users(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[UserWithRoles]:
    """
    Busca usuarios por nombre o email
    """
    try:
        search_filter = or_(
            User.full_name.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%")
        )
        
        users = db.query(User).filter(
            and_(User.deleted_at.is_(None), search_filter)
        ).offset(skip).limit(limit).all()
        
        result = []
        for user in users:
            user_roles = get_user_roles(db, user.id)
            user_with_roles = UserWithRoles(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                status=user.status,
                created_at=user.created_at,
                roles=user_roles
            )
            result.append(user_with_roles)
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching users"
        )
    
def activate_user(db: Session, user_id: UUID) -> ActionResponse:
    """
    Activa un usuario cambiando su estado a 'active'.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario a activar
        
    Returns:
        ActionResponse: Respuesta de la acción realizada
        
    Raises:
        HTTPException: Si el usuario no existe o ya está eliminado
    """
    try:
        # Buscar el usuario
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verificar si ya está activo
        if user.status == "active":
            return ActionResponse(
                success=True,
                detail="User is already active",
                data={"user_id": str(user_id), "status": "active"}
            )
        
        # Activar usuario
        user.status = "active"
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user_id} activated successfully")
        
        return ActionResponse(
            success=True,
            detail="User activated successfully",
            data={"user_id": str(user_id), "status": "active"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating user"
        )

def suspend_user(db: Session, user_id: UUID) -> ActionResponse:
    """
    Suspende un usuario cambiando su estado a 'suspended'.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario a suspender
        
    Returns:
        ActionResponse: Respuesta de la acción realizada
        
    Raises:
        HTTPException: Si el usuario no existe o ya está eliminado
    """
    try:
        # Buscar el usuario
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verificar si ya está suspendido
        if user.status == "suspended":
            return ActionResponse(
                success=True,
                detail="User is already suspended",
                data={"user_id": str(user_id), "status": "suspended"}
            )
        
        # Suspender usuario
        user.status = "suspended"
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user_id} suspended successfully")
        
        return ActionResponse(
            success=True,
            detail="User suspended successfully",
            data={"user_id": str(user_id), "status": "suspended"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error suspending user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error suspending user"
        )
    
def set_user_status(db: Session, user_id: UUID, new_status: str) -> ActionResponse:
    """
    Cambia el estado de un usuario a un estado específico.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        new_status: Nuevo estado ('active', 'pending', 'suspended')
        
    Returns:
        ActionResponse: Respuesta de la acción realizada
        
    Raises:
        HTTPException: Si el usuario no existe, está eliminado o el estado es inválido
    """
    try:
        # Validar estado
        valid_statuses = ["active", "pending", "suspended"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Buscar el usuario
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verificar si ya tiene el estado solicitado
        if user.status == new_status:
            return ActionResponse(
                success=True,
                detail=f"User already has status: {new_status}",
                data={"user_id": str(user_id), "status": new_status}
            )
        
        # Cambiar estado
        old_status = user.status
        user.status = new_status
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user_id} status changed from {old_status} to {new_status}")
        
        return ActionResponse(
            success=True,
            detail=f"User status changed to {new_status} successfully",
            data={
                "user_id": str(user_id), 
                "old_status": old_status,
                "new_status": new_status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing user {user_id} status to {new_status}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing user status"
        )
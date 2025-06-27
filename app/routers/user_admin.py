#/////////////////////////// Sistema usuarios invitados ///////////////////////////
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Any
from uuid import UUID

from app.core.database import get_db
from app.dependencies import get_super_admin, get_school_admin, get_teacher, get_inventory_manager
from app.models.user import UserWithRoles, UserUpdate, ActionResponse
from app.services.user_admin import (
    list_users,
    get_user_by_id,
    update_user,
    block_user,
    activate_user,
    suspend_user,
    search_users
)
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/admin-users",
    tags=["admin-users"],
    dependencies=[Depends(get_super_admin)]
)

@router.get("", response_model=List[UserWithRoles])
async def list_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, pending, suspended"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los usuarios del sistema con sus roles.
    Solo accesible para superadministradores.
    
    - **skip**: Número de registros a omitir (paginación)
    - **limit**: Número máximo de registros a retornar
    - **search**: Búsqueda por nombre o email (opcional)
    - **status_filter**: Filtrar por estado del usuario (opcional)
    """
    try:
        if search:
            logger.info(f"Searching users with query: {search}")
            return search_users(db, search, skip, limit, status_filter)
        else:
            logger.info(f"Listing users (skip: {skip}, limit: {limit}, status: {status_filter})")
            return list_users(db, skip, limit)
    except Exception as e:
        import traceback
        logger.error(f"Error in list_all_users: {str(e)}\n{traceback.format_exc()}")
        logger.error(f"Error in list_all_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )

@router.get("/stats", response_model=dict)
async def get_user_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas básicas de usuarios del sistema.
    """
    try:
        # Contar usuarios por estado
        stats = db.query(
            User.status,
            func.count(User.id).label('count')
        ).filter(
            User.deleted_at.is_(None)
        ).group_by(User.status).all()
        
        # Contar usuarios eliminados
        deleted_count = db.query(func.count(User.id)).filter(
            User.deleted_at.is_not(None)
        ).scalar()
        
        result = {
            "active_users": 0,
            "pending_users": 0,
            "suspended_users": 0,
            "deleted_users": deleted_count,
            "total_users": 0
        }
        
        for stat in stats:
            count = stat.count
            if stat.status == "active":
                result["active_users"] = count
            elif stat.status == "pending":
                result["pending_users"] = count
            elif stat.status == "suspended":
                result["suspended_users"] = count
            
            result["total_users"] += count
        
        logger.info(f"User stats retrieved: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user statistics"
        )

@router.get("/{user_id}", response_model=UserWithRoles)
async def get_user_details(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de un usuario específico por su ID.
    Incluye información de roles asignados.
    
    - **user_id**: ID único del usuario
    """
    try:
        logger.info(f"Getting user details for: {user_id}")
        return get_user_by_id(db, user_id)
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        raise

@router.patch("/{user_id}", response_model=UserWithRoles)
async def update_user_details(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza los datos de un usuario existente.
    Permite cambiar nombre, email y otros campos.
    
    - **user_id**: ID único del usuario
    - **full_name**: Nuevo nombre completo (opcional)
    - **email**: Nuevo email (opcional)
    - **status**: Nuevo estado (opcional)
    """
    try:
        logger.info(f"Updating user {user_id} with data: {user_data.dict(exclude_unset=True)}")
        return update_user(db, user_id, user_data)
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise

@router.post("/{user_id}/activate", response_model=ActionResponse)
async def activate_user_account(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Activa una cuenta de usuario.
    Cambia el estado del usuario a 'active'.
    
    - **user_id**: ID único del usuario a activar
    """
    try:
        logger.info(f"Activating user: {user_id}")
        return activate_user(db, user_id)
    except Exception as e:
        logger.error(f"Error activating user {user_id}: {str(e)}")
        raise

@router.post("/{user_id}/suspend", response_model=ActionResponse)
async def suspend_user_account(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Suspende una cuenta de usuario.
    Cambia el estado del usuario a 'suspended'.
    
    - **user_id**: ID único del usuario a suspender
    """
    try:
        logger.info(f"Suspending user: {user_id}")
        return suspend_user(db, user_id)
    except Exception as e:
        logger.error(f"Error suspending user {user_id}: {str(e)}")
        raise

@router.post("/{user_id}/set-pending", response_model=ActionResponse)
async def set_user_pending(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Pone un usuario en estado pendiente.
    Cambia el estado del usuario a 'pending'.
    
    - **user_id**: ID único del usuario
    """
    try:
        from app.services.user_admin import set_user_status # <-- cambiar esto
        logger.info(f"Setting user {user_id} to pending")
        return set_user_status(db, user_id, "pending")
    except Exception as e:
        logger.error(f"Error setting user {user_id} to pending: {str(e)}")
        raise

@router.delete("/{user_id}", response_model=ActionResponse)
async def delete_user_account(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_super_admin)
):
    """
    Bloquea/elimina un usuario del sistema (soft delete).
    El usuario se marca como eliminado pero se conservan sus datos.
    
    - **user_id**: ID único del usuario a eliminar
    """
    try:
        # Prevenir auto-eliminación
        if hasattr(current_user, 'id') and current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself"
            )
        
        logger.info(f"Deleting user: {user_id}")
        return block_user(db, user_id)
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise
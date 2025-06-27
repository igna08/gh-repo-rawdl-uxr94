
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.invitation import InvitationCreate, InvitationRead
from app.services import invitation_service
from app.models.user import User
from app.models.role import Role, RoleEnum # Assuming RoleEnum is here
from app.models.user_role import UserRole
from app.services.auth_service import get_current_user # Assuming this exists and is appropriate for now
from app.services.email_service import send_invitation_email  # Assuming this function exists

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
async def create_new_invitation(
    invitation_in: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> InvitationRead:
    """
    Creates a new invitation.
    Only accessible by users with the SUPER_ADMIN role.
    Luego de crear la invitación, envía un correo Gmail al invitado con el token.
    """
    try:
        # 1. Verificar rol SUPER_ADMIN
        # CORREGIDO: Usar el valor del enum directamente si RoleEnum es un Enum
        super_admin_role_stmt = select(Role).where(Role.name == RoleEnum.SUPER_ADMIN.value)
        # O si RoleEnum.SUPER_ADMIN es directamente el ID:
        # super_admin_role_stmt = select(Role).where(Role.id == RoleEnum.SUPER_ADMIN)
        
        super_admin_role = db.execute(super_admin_role_stmt).scalar_one_or_none()

        if not super_admin_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Super admin role not found."
            )

        # CORREGIDO: Usar scalar_one_or_none() para mayor claridad
        user_role_stmt = select(UserRole).where(
            UserRole.user_id == current_user.id,
            UserRole.role_id == super_admin_role.id
        )
        user_is_super_admin = db.execute(user_role_stmt).scalar_one_or_none()

        if not user_is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create invitations."
            )

        # 2. Crear la invitación en la base de datos
        invitation_orm = invitation_service.create_invitation(
            db=db,
            invitation_in=invitation_in,
            sent_by=current_user.id
        )

        # 3. Enviar correo de invitación
        # CORREGIDO: Manejar posibles errores de envío de email
        try:
            send_invitation_email(
                recipient_email=invitation_in.email,
                invitation_token=str(invitation_orm.token)
            )
        except Exception as email_error:
            print(f"ERROR AL ENVIAR EMAIL: {repr(email_error)}")
            # Opcional: podrías decidir si esto debe fallar todo el proceso
            # o solo registrar el error y continuar
            # raise HTTPException(
            #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #     detail="Invitation created but email could not be sent."
            # )

        return invitation_orm

    except HTTPException as e:
        # Re-lanzar errores HTTP conocidos
        raise e
    except Exception as e:
        print(f"ERROR AL CREAR INVITACION: {repr(e)}")  # CORREGIDO: Indentación
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the invitation."
        )


@router.get("/{token}", response_model=InvitationRead)
async def get_invitation_info(
    token: UUID,
    db: Session = Depends(get_db)
) -> InvitationRead:
    """
    Retrieves information about an invitation using its token.
    """
    try:
        invitation_orm = invitation_service.get_invitation_by_token(db=db, token=token)

        if not invitation_orm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found or has expired."
            )
        
        # The 'is_valid' property from the ORM model will be automatically accessed by Pydantic.
        return invitation_orm
    
    except HTTPException as e:
        # Re-lanzar errores HTTP conocidos
        raise e
    except Exception as e:
        print(f"ERROR AL OBTENER INVITACION: {repr(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the invitation."
        )


# FUNCIONES AUXILIARES ADICIONALES (OPCIONALES)
# Estas funciones pueden ayudar a hacer el código más limpio y reutilizable

async def verify_super_admin_role(current_user: User, db: Session) -> None:
    """
    Verifica si el usuario actual tiene rol SUPER_ADMIN.
    Lanza HTTPException si no lo tiene.
    """
    super_admin_role_stmt = select(Role).where(Role.name == RoleEnum.SUPER_ADMIN.value)
    super_admin_role = db.execute(super_admin_role_stmt).scalar_one_or_none()

    if not super_admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Super admin role not found in system."
        )

    user_role_stmt = select(UserRole).where(
        UserRole.user_id == current_user.id,
        UserRole.role_id == super_admin_role.id
    )
    user_is_super_admin = db.execute(user_role_stmt).scalar_one_or_none()

    if not user_is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from pydantic import BaseModel
from typing import Any

from app.models.user import UserRead, UserWithRoles

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserWithRoles)
async def read_users_me(current: dict = Depends(get_current_user)):
    """
    Get the current logged-in user's details, incluyendo flags de cada rol.
    """
    user: Any = current["user"]
    roles_dict: dict = current["roles"]

    # Serializamos el usuario base
    base_data = UserRead.model_validate(user).model_dump()

    return {
        **base_data,
        "roles": roles_dict
    }


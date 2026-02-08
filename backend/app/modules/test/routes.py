"""
Test endpoints to verify authentication.
"""
from app.core.dependencies import get_current_active_user
from app.modules.auth.models import User
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/test", tags=["Testing"])


@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """
    Protected endpoint requiring authentication.

    Returns:
        User info
    """
    return {
        "message": "This is a protected route",
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "role": current_user.role,
        },
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user info.

    Returns:
        Current user details
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
    }

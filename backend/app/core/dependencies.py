# backend/app/core/dependencies.py

from typing import cast

from app.modules.auth.models import Role, User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session
from typing import List
from fastapi import Depends, HTTPException, status

from .database import get_db
from .security import decode_token

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None:
            raise credentials_exception

        # Verify token type
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Access token required.",
            )

        # Get user ID from token
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    user = cast(User | None, db.query(User).filter(User.id == user_id).first())

    if user is None:
        raise credentials_exception

    # Check if user is deleted (GDPR)
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deleted",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (not deleted).

    Args:
        current_user: Current user from token

    Returns:
        Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


# ============================================================================
# ROLE-BASED DEPENDENCIES
# ============================================================================


def require_role(allowed_roles: list[Role]):
    """
    Dependency factory to check if user has required role.

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker

#Tharin - 10/02/2026
def require_permission(required_permissions: List[str]):
    """
    Dependency to check if user has required permissions
    """
    async def permission_checker(current_user = Depends(get_current_user)):
        # For now, allow all authenticated users
        # You can enhance this later with actual permission checking
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_checker


# Convenience dependencies for specific roles
get_current_admin = require_role([Role.ADMIN])
get_current_customer = require_role([Role.CUSTOMER, Role.ADMIN])
get_current_exporter = require_role([Role.EXPORTER, Role.ADMIN])
get_current_clearing_agent = require_role([Role.CLEARING_AGENT, Role.ADMIN])
get_current_finance_partner = require_role([Role.FINANCE_PARTNER, Role.ADMIN])

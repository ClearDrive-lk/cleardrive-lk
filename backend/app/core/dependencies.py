# backend/app/core/dependencies.py

from typing import cast

from app.core.redis import is_token_blacklisted
from app.modules.auth.models import Role, User
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from .database import get_db
from .security import decode_access_token

# HTTP Bearer token scheme
# auto_error=False lets us return a consistent 401 instead of FastAPI's default 403
# when the Authorization header is missing.
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.

    Also stores token JTI in request.state for logout and blacklist checking.

    Security checks:
    1. Decode and validate JWT token
    2. Verify token type is 'access'
    3. Check if token is blacklisted (logged out)
    4. Verify user exists and is not deleted
    5. Store JTI in request state for logout

    Args:
        request: HTTP request (for storing token JTI)
        credentials: HTTP Authorization header with Bearer token
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException 401: Invalid, expired, or blacklisted token
        HTTPException 403: User account deleted
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        # Decode token
        token = credentials.credentials
        payload = decode_access_token(token)

        if payload is None:
            raise credentials_exception

        # Verify token type (prevent refresh token misuse)
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user ID and JTI from token
        user_id: str | None = payload.get("sub")
        token_jti: str | None = payload.get("jti")

        if user_id is None:
            raise credentials_exception

        # Check if token is blacklisted (logged out)
        if token_jti and await is_token_blacklisted(token_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

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

    # Store token JTI in request state for logout
    if token_jti:
        request.state.token_jti = token_jti

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (not deleted or inactive).

    Args:
        current_user: Current user from token

    Returns:
        Current active user

    Raises:
        HTTPException 403: If user is inactive or deleted
    """
    # Check if user is deleted
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Check if user has is_active field and it's False
    if hasattr(current_user, "is_active") and not current_user.is_active:
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

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role([Role.ADMIN]))):
            ...

    Args:
        allowed_roles: List of allowed roles

    Returns:
        Dependency function that validates user role
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


# ============================================================================
# CONVENIENCE DEPENDENCIES FOR SPECIFIC ROLES
# ============================================================================

# Admin only access
get_current_admin = require_role([Role.ADMIN])

# Customer or admin access
get_current_customer = require_role([Role.CUSTOMER, Role.ADMIN])

# Exporter or admin access
get_current_exporter = require_role([Role.EXPORTER, Role.ADMIN])

# Clearing agent or admin access
get_current_clearing_agent = require_role([Role.CLEARING_AGENT, Role.ADMIN])

# Finance partner or admin access
get_current_finance_partner = require_role([Role.FINANCE_PARTNER, Role.ADMIN])

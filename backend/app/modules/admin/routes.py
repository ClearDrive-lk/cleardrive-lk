"""
Admin user management endpoints.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.core.dependencies import get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import Role, User
from app.modules.kyc.models import KYCDocument, KYCStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────


class UserListItem(BaseModel):
    """User item in list response."""

    id: str
    email: str
    name: str
    role: str
    kyc_status: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response with pagination."""

    users: List[UserListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class RoleChangeRequest(BaseModel):
    """Request to change user role."""

    role: str
    reason: str


class RoleChangeResponse(BaseModel):
    """Response after role change."""

    message: str
    user_id: str
    old_role: str
    new_role: str
    changed_by: str
    changed_at: str


# ─────────────────────────────────────────────────────────────────────────────
# GET /admin/users - List all users with filters
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/users", response_model=UserListResponse)
async def get_users(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    # Search
    search: Optional[str] = Query(None, description="Search by name or email"),
    # Filters
    role: Optional[str] = Query(None, description="Filter by role"),
    kyc_status: Optional[str] = Query(
        None, description="Filter by KYC status (PENDING, APPROVED, REJECTED, NONE)"
    ),
    created_after: Optional[str] = Query(None, description="Filter by creation date (ISO format)"),
    created_before: Optional[str] = Query(None, description="Filter by creation date (ISO format)"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    # Dependencies
    current_user: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """
    Get all users with pagination, search, and filters.

    Permissions: manage_users

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - search: Search by name or email (case-insensitive)
    - role: Filter by role (CUSTOMER, ADMIN, EXPORTER, CLEARING_AGENT, FINANCE_PARTNER)
    - kyc_status: Filter by KYC status (PENDING, APPROVED, REJECTED, NONE)
    - created_after: Filter by creation date (ISO format, e.g., 2026-01-01T00:00:00)
    - created_before: Filter by creation date (ISO format)
    - sort_by: Sort field (created_at, email, name, role)
    - sort_order: Sort order (asc, desc)

    Returns:
        Paginated list of users with metadata

    Examples:
        GET /admin/users?search=john&role=CUSTOMER
        GET /admin/users?kyc_status=PENDING&page=2
        GET /admin/users?created_after=2026-01-01T00:00:00&sort_by=email
    """
    # Start with base query
    query = db.query(User)

    # Apply search filter
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Apply role filter
    if role:
        try:
            role_enum = Role(role)
            query = query.filter(User.role == role_enum)
        except ValueError:
            valid_roles = [r.value for r in Role]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid role: {role}. Valid roles: {valid_roles}",
            )

    # Apply KYC status filter
    if kyc_status:
        # Join with KYC documents
        query = query.join(KYCDocument, KYCDocument.user_id == User.id, isouter=True)

        if kyc_status == "NONE":
            # Users without KYC documents
            query = query.filter(KYCDocument.id.is_(None))
        else:
            try:
                kyc_status_enum = KYCStatus(kyc_status)
                query = query.filter(KYCDocument.status == kyc_status_enum)
            except ValueError:
                valid_statuses = [s.value for s in KYCStatus]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid KYC status: {kyc_status}. Valid statuses: {valid_statuses} or NONE",
                )

    # Apply date range filters
    if created_after:
        try:
            date_after = datetime.fromisoformat(created_after)
            query = query.filter(User.created_at >= date_after)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid created_after date format. Use ISO format (e.g., 2026-01-01T00:00:00)",
            )

    if created_before:
        try:
            date_before = datetime.fromisoformat(created_before)
            query = query.filter(User.created_at <= date_before)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid created_before date format. Use ISO format (e.g., 2026-01-01T00:00:00)",
            )

    # Get total count before pagination
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    # Explicitly reject out-of-range pages to avoid confusing empty responses.
    if total > 0 and page > total_pages:
        raise HTTPException(
            status_code=400,
            detail=f"Page {page} out of range. Last page is {total_pages}.",
        )

    # Apply sorting
    sort_columns = {
        "created_at": User.created_at,
        "email": User.email,
        "name": User.name,
        "role": User.role,
    }

    sort_column = sort_columns.get(sort_by, User.created_at)

    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute query
    users = query.all()

    # Get KYC status for each user (if not already joined)
    if not kyc_status:
        user_ids = [str(user.id) for user in users]
        kyc_docs = db.query(KYCDocument).filter(KYCDocument.user_id.in_(user_ids)).all()
        kyc_map = {str(doc.user_id): doc.status.value for doc in kyc_docs}
    else:
        kyc_map = {}

    # Build response
    user_list = [
        UserListItem(
            id=str(user.id),
            email=user.email,
            name=user.name or "N/A",
            role=user.role.value,
            kyc_status=kyc_map.get(str(user.id)),
            created_at=user.created_at.isoformat(),
            last_login=user.updated_at.isoformat() if user.updated_at else None,
            is_active=user.deleted_at is None,
        )
        for user in users
    ]

    # Log admin action
    logger.info(
        f"Admin {current_user.email} listed users: {total} total, page {page}/{total_pages}",
        extra={
            "admin_id": str(current_user.id),
            "admin_email": current_user.email,
            "total_users": total,
            "page": page,
            "filters": {
                "search": search,
                "role": role,
                "kyc_status": kyc_status,
            },
        },
    )

    return UserListResponse(
        users=user_list,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /admin/users/{user_id}/role - Change user role
# ─────────────────────────────────────────────────────────────────────────────


@router.patch("/users/{user_id}/role", response_model=RoleChangeResponse)
async def change_user_role(
    user_id: UUID,
    request: RoleChangeRequest,
    current_user: User = Depends(require_permission(Permission.MANAGE_ROLES)),
    db: Session = Depends(get_db),
):
    """
    Change a user's role.

    Permissions: manage_roles

    Security:
    - Admins cannot change their own role (prevents privilege escalation)
    - All role changes are logged as security events
    - Reason is required (minimum 10 characters)
    - Invalid roles are rejected

    Args:
        user_id: UUID of user to modify
        request: New role and reason for change
        current_user: Admin making the change
        db: Database session

    Returns:
        Role change confirmation with audit information

    Raises:
        HTTPException 404: User not found
        HTTPException 400: Invalid role, cannot change own role, or insufficient reason
        HTTPException 403: Insufficient permissions (requires manage_roles)

    Examples:
        PATCH /admin/users/123e4567-e89b-12d3-a456-426614174000/role
        Body: {
            "role": "ADMIN",
            "reason": "Promoting user to admin role due to increased responsibilities"
        }
    """
    # Get user to modify
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admins from changing their own role (security measure)
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role. Ask another admin to modify your permissions.",
        )

    # Validate new role
    try:
        new_role = Role(request.role)
    except ValueError:
        valid_roles = [r.value for r in Role]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role: {request.role}. Valid roles: {valid_roles}",
        )

    # Check if role is actually changing
    if user.role == new_role:
        raise HTTPException(status_code=400, detail=f"User already has role: {new_role.value}")

    # Validate reason is provided and sufficient
    if not request.reason or len(request.reason.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Reason is required and must be at least 10 characters",
        )

    # Store old role for audit log
    old_role = user.role

    # Update user role
    user.role = new_role
    user.updated_at = datetime.utcnow()

    # Persist role change
    db.commit()
    db.refresh(user)

    # Log security event
    logger.warning(
        f"Role changed: {user.email} from {old_role.value} to {new_role.value} by {current_user.email}",
        extra={
            "admin_id": str(current_user.id),
            "admin_email": current_user.email,
            "user_id": str(user.id),
            "user_email": user.email,
            "old_role": old_role.value,
            "new_role": new_role.value,
            "reason": request.reason,
            "security_event": "role_changed",
        },
    )

    return RoleChangeResponse(
        message="Role changed successfully",
        user_id=str(user.id),
        old_role=old_role.value,
        new_role=new_role.value,
        changed_by=current_user.email,
        changed_at=datetime.utcnow().isoformat(),
    )

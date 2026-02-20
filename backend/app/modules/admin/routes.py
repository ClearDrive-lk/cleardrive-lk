"""
Admin user management endpoints.
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.core.dependencies import get_current_active_user, get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import Role, User
from app.modules.kyc.models import KYCDocument, KYCStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────


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


# ─────────────────────────────────────────────
# GET /admin/users
# ─────────────────────────────────────────────


@router.get("/users", response_model=UserListResponse)
async def get_users(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    # Search
    search: Optional[str] = Query(None, description="Search by name or email"),
    # Filters
    role: Optional[str] = Query(None, description="Filter by role"),
    kyc_status: Optional[str] = Query(None, description="Filter by KYC status"),
    created_after: Optional[str] = Query(None, description="Filter by creation date (ISO format)"),
    created_before: Optional[str] = Query(None, description="Filter by creation date (ISO format)"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    # Dependencies
    current_user: User = Depends(get_current_active_user),
    _: User = Depends(require_permission(Permission.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """
    Get all users with pagination, search, and filters.

    Permissions: manage_users

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - search: Search by name or email
    - role: Filter by role (CUSTOMER, ADMIN, etc.)
    - kyc_status: Filter by KYC status (PENDING, APPROVED, REJECTED)
    - created_after: Filter by creation date (ISO format)
    - created_before: Filter by creation date (ISO format)
    - sort_by: Sort field (created_at, email, name, role)
    - sort_order: Sort order (asc, desc)

    Returns:
        Paginated list of users with metadata
    """
    query = db.query(User)

    if search:
        query = query.filter(or_(User.name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%")))

    if role:
        try:
            query = query.filter(User.role == Role(role))
        except ValueError:
            raise HTTPException(400, f"Invalid role: {role}")

    if kyc_status:
        query = query.join(KYCDocument, KYCDocument.user_id == User.id, isouter=True)
        if kyc_status == "NONE":
            query = query.filter(KYCDocument.id.is_(None))
        else:
            try:
                query = query.filter(KYCDocument.status == KYCStatus(kyc_status))
            except ValueError:
                raise HTTPException(400, f"Invalid KYC status: {kyc_status}")

    if created_after:
        try:
            query = query.filter(User.created_at >= datetime.fromisoformat(created_after))
        except ValueError:
            raise HTTPException(400, "Invalid created_after date format. Use ISO format.")

    if created_before:
        try:
            query = query.filter(User.created_at <= datetime.fromisoformat(created_before))
        except ValueError:
            raise HTTPException(400, "Invalid created_before date format. Use ISO format.")

    total = query.count()

    sort_column = {
        "created_at": User.created_at,
        "email": User.email,
        "name": User.name,
        "role": User.role,
    }.get(sort_by, User.created_at)

    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
    users = query.offset((page - 1) * limit).limit(limit).all()

    if not kyc_status:
        user_ids = [str(u.id) for u in users]
        kyc_docs = db.query(KYCDocument).filter(KYCDocument.user_id.in_(user_ids)).all()
        kyc_map = {str(doc.user_id): doc.status.value for doc in kyc_docs}
    else:
        kyc_map = {}

    user_list = [
        UserListItem(
            id=str(u.id),
            email=u.email,
            name=u.name or "N/A",
            role=u.role.value,
            kyc_status=kyc_map.get(str(u.id)),
            created_at=u.created_at.isoformat(),
            last_login=u.updated_at.isoformat() if u.updated_at else None,
            is_active=u.deleted_at is None,
        )
        for u in users
    ]

    total_pages = (total + limit - 1) // limit

    logger.info(
        f"Admin {current_user.email} listed users: {total} total, page {page}/{total_pages}",
        extra={"admin_id": str(current_user.id), "total_users": total, "page": page},
    )

    return UserListResponse(
        users=user_list, total=total, page=page, limit=limit, total_pages=total_pages
    )


# ─────────────────────────────────────────────
# PATCH /admin/users/{user_id}/role
# ─────────────────────────────────────────────


@router.patch("/users/{user_id}/role", response_model=RoleChangeResponse)
async def change_user_role(
    user_id: str,
    request: RoleChangeRequest,
    current_user: User = Depends(get_current_active_user),
    _: User = Depends(require_permission(Permission.MANAGE_ROLES)),
    db: Session = Depends(get_db),
):
    """
    Change a user's role.

    Permissions: manage_roles

    Args:
        user_id: UUID of user to modify
        request: New role and reason
        current_user: Admin making the change
        db: Database session

    Returns:
        Role change confirmation with audit info

    Raises:
        HTTPException 404: User not found
        HTTPException 400: Invalid role or cannot change own role
        HTTPException 403: Insufficient permissions
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if str(user.id) == str(current_user.id):
        raise HTTPException(
            400, "Cannot change your own role. Ask another admin to modify your permissions."
        )

    try:
        new_role = Role(request.role)
    except ValueError:
        raise HTTPException(
            400, f"Invalid role: {request.role}. Valid roles: {[r.value for r in Role]}"
        )

    if user.role == new_role:
        raise HTTPException(400, f"User already has role: {new_role.value}")

    if not request.reason or len(request.reason.strip()) < 10:
        raise HTTPException(400, "Reason is required and must be at least 10 characters")

    old_role = user.role
    user.role = new_role
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    logger.warning(
        f"Role changed: {user.email} from {old_role.value} to {new_role.value} by {current_user.email}",
        extra={
            "admin_id": str(current_user.id),
            "user_id": str(user.id),
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

# backend/app/core/permissions.py

import logging
from enum import Enum
from functools import wraps
from typing import List, Optional, Set, Union, cast
from uuid import UUID

from app.modules.auth.models import Role, User
from fastapi import Depends, HTTPException, status

from .dependencies import get_current_active_user

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """
    All system permissions in ClearDrive.lk.

    Naming Convention:
    - <action>_<resource>
    - Examples: view_vehicles, create_order, approve_kyc
    """

    # ============== VEHICLE PERMISSIONS ==============
    VIEW_VEHICLES = "view_vehicles"
    MANAGE_VEHICLES = "manage_vehicles"  # CRUD operations

    # ============== ORDER PERMISSIONS ==============
    CREATE_ORDER = "create_order"
    VIEW_OWN_ORDERS = "view_own_orders"
    VIEW_ALL_ORDERS = "view_all_orders"
    MANAGE_ORDERS = "manage_orders"  # Update, delete
    CANCEL_OWN_ORDER = "cancel_own_order"
    OVERRIDE_ORDER_STATUS = "override_status"  # Admin only

    # ============== KYC PERMISSIONS ==============
    SUBMIT_KYC = "submit_kyc"
    VIEW_OWN_KYC = "view_own_kyc"
    REVIEW_KYC = "review_kyc"
    APPROVE_KYC = "approve_kyc"
    REJECT_KYC = "reject_kyc"

    # ============== PAYMENT PERMISSIONS ==============
    MAKE_PAYMENT = "make_payment"
    VIEW_OWN_PAYMENTS = "view_own_payments"
    VIEW_ALL_PAYMENTS = "view_all_payments"
    REFUND_PAYMENT = "refund_payment"

    # ============== FINANCE PERMISSIONS ==============
    REQUEST_FINANCE = "request_finance"
    VIEW_FINANCE_REQUESTS = "view_finance_requests"
    APPROVE_FINANCE = "approve_finance"
    REJECT_FINANCE = "reject_finance"

    # ============== INSURANCE PERMISSIONS ==============
    REQUEST_INSURANCE = "request_insurance"
    VIEW_INSURANCE_REQUESTS = "view_insurance_requests"
    APPROVE_INSURANCE = "approve_insurance"
    REJECT_INSURANCE = "reject_insurance"

    # ============== LC (LETTER OF CREDIT) PERMISSIONS ==============
    REQUEST_LC = "request_lc"
    VIEW_LC_REQUESTS = "view_lc_requests"
    APPROVE_LC = "approve_lc"
    REJECT_LC = "reject_lc"

    # ============== SHIPPING/EXPORTER PERMISSIONS ==============
    VIEW_ASSIGNED_ORDERS = "view_assigned_orders"
    UPDATE_SHIPPING_DETAILS = "update_shipping_details"
    UPLOAD_SHIPMENT_DOCUMENTS = "upload_shipment_documents"
    MARK_ORDER_SHIPPED = "mark_order_shipped"
    VIEW_EXPORT_TASKS = "view_export_tasks"
    VIEW_EXPORT_HISTORY = "view_export_history"
    ASSIGN_EXPORTER = "assign_exporter"
    APPROVE_SHIPMENT = "approve_shipment"
    VERIFY_SHIPPING_DOCS = "verify_shipping_docs"

    # ============== CLEARING AGENT PERMISSIONS ==============
    VIEW_CLEARANCE_TASKS = "view_clearance_tasks"
    MANAGE_CLEARANCE = "manage_clearance"
    UPLOAD_CUSTOMS_DOCUMENTS = "upload_customs_documents"
    UPDATE_SHIPMENT_STATUS = "update_shipment_status"
    ASSIGN_CLEARING_AGENT = "assign_clearing_agent"

    # ============== ADMIN PERMISSIONS ==============
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SYSTEM = "manage_system"
    MANAGE_TAX_RULES = "manage_tax_rules"
    APPROVE_TAX_RULES = "approve_tax_rules"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SECURITY_EVENTS = "manage_security_events"
    VERIFY_FILE_INTEGRITY = "verify_file_integrity"

    # ============== DOCUMENT PERMISSIONS ==============
    UPLOAD_DOCUMENTS = "upload_documents"
    VIEW_OWN_DOCUMENTS = "view_own_documents"
    VIEW_ALL_DOCUMENTS = "view_all_documents"

    # ============== PROFILE PERMISSIONS ==============
    VIEW_OWN_PROFILE = "view_own_profile"
    EDIT_OWN_PROFILE = "edit_own_profile"

    # ============== GDPR PERMISSIONS ==============
    EXPORT_OWN_DATA = "export_own_data"
    DELETE_OWN_DATA = "delete_own_data"


# ============================================================================
# ROLE-PERMISSION MAPPING (Using Sets for Better Performance)
# ============================================================================

ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    # CUSTOMER PERMISSIONS (Basic user)
    Role.CUSTOMER: {
        # Vehicles
        Permission.VIEW_VEHICLES,
        # Orders
        Permission.CREATE_ORDER,
        Permission.VIEW_OWN_ORDERS,
        Permission.CANCEL_OWN_ORDER,
        # KYC
        Permission.SUBMIT_KYC,
        Permission.VIEW_OWN_KYC,
        # Payments
        Permission.MAKE_PAYMENT,
        Permission.VIEW_OWN_PAYMENTS,
        # Finance & Insurance
        Permission.REQUEST_FINANCE,
        Permission.REQUEST_INSURANCE,
        Permission.REQUEST_LC,
        # Documents
        Permission.UPLOAD_DOCUMENTS,
        Permission.VIEW_OWN_DOCUMENTS,
        # Profile
        Permission.VIEW_OWN_PROFILE,
        Permission.EDIT_OWN_PROFILE,
        # GDPR
        Permission.EXPORT_OWN_DATA,
        Permission.DELETE_OWN_DATA,
    },
    # ADMIN PERMISSIONS (All permissions - wildcard)
    Role.ADMIN: set(Permission),  # Admin has ALL permissions automatically
    # CLEARING AGENT PERMISSIONS
    Role.CLEARING_AGENT: {
        Permission.VIEW_VEHICLES,
        Permission.VIEW_ASSIGNED_ORDERS,
        Permission.VIEW_CLEARANCE_TASKS,
        Permission.MANAGE_CLEARANCE,
        Permission.UPLOAD_CUSTOMS_DOCUMENTS,
        Permission.UPDATE_SHIPMENT_STATUS,
        Permission.VIEW_OWN_PROFILE,
        Permission.EDIT_OWN_PROFILE,
    },
    # FINANCE PARTNER PERMISSIONS
    Role.FINANCE_PARTNER: {
        Permission.VIEW_FINANCE_REQUESTS,
        Permission.APPROVE_FINANCE,
        Permission.REJECT_FINANCE,
        Permission.VIEW_INSURANCE_REQUESTS,
        Permission.APPROVE_INSURANCE,
        Permission.REJECT_INSURANCE,
        Permission.VIEW_OWN_PROFILE,
        Permission.EDIT_OWN_PROFILE,
    },
    # EXPORTER PERMISSIONS
    Role.EXPORTER: {
        Permission.VIEW_ASSIGNED_ORDERS,
        Permission.UPDATE_SHIPPING_DETAILS,
        Permission.UPLOAD_SHIPMENT_DOCUMENTS,
        Permission.MARK_ORDER_SHIPPED,
        Permission.VIEW_EXPORT_TASKS,
        Permission.VIEW_EXPORT_HISTORY,
        Permission.VIEW_OWN_PROFILE,
        Permission.EDIT_OWN_PROFILE,
    },
}


# ============================================================================
# PERMISSION HELPER FUNCTIONS
# ============================================================================


def get_role_permissions(role: Role) -> Set[Permission]:
    """
    Get all permissions for a role.

    Args:
        role: User role

    Returns:
        Set of permissions for that role
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has a specific permission.

    Uses Set lookup for O(1) performance.

    Args:
        user: User object
        permission: Permission to check

    Returns:
        True if user has permission, False otherwise
    """
    role = cast(Role, user.role)
    user_permissions = get_role_permissions(role)
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """
    Check if user has ANY of the specified permissions.

    Args:
        user: User object
        permissions: List of permissions to check

    Returns:
        True if user has at least one permission
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """
    Check if user has ALL of the specified permissions.

    Args:
        user: User object
        permissions: List of permissions to check

    Returns:
        True if user has all permissions
    """
    return all(has_permission(user, perm) for perm in permissions)


def get_user_permissions(user: User) -> Set[Permission]:
    """
    Get all permissions for a user.

    Useful for permission debugging and UI rendering.

    Args:
        user: User object

    Returns:
        Set of all user's permissions
    """
    role = cast(Role, user.role)
    return get_role_permissions(role)


# ============================================================================
# FASTAPI DEPENDENCY-BASED PERMISSION CHECKERS
# ============================================================================


def require_permission(permission: Permission):
    """
    Dependency to require a specific permission.

    Usage:
        @router.get("/admin/users")
        async def get_users(user: User = Depends(require_permission(Permission.MANAGE_USERS))):
            ...

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """

    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission.value}",
            )
        return user

    return permission_checker


def require_any_permission_dep(permissions: List[Permission]):
    """
    Dependency to require ANY of the specified permissions.

    Usage:
        @router.get("/finance/requests")
        async def get_requests(
            user: User = Depends(require_any_permission_dep([
                Permission.VIEW_FINANCE_REQUESTS,
                Permission.VIEW_INSURANCE_REQUESTS
            ]))
        ):
            ...

    Args:
        permissions: List of permissions (user needs at least one)

    Returns:
        Dependency function
    """

    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        if not has_any_permission(user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required (any): {[p.value for p in permissions]}",
            )
        return user

    return permission_checker


def require_all_permissions_dep(permissions: List[Permission]):
    """
    Dependency to require ALL of the specified permissions.

    Usage:
        @router.post("/admin/tax-rules/approve")
        async def approve_tax_rule(
            user: User = Depends(require_all_permissions_dep([
                Permission.MANAGE_TAX_RULES,
                Permission.APPROVE_TAX_RULES
            ]))
        ):
            ...

    Args:
        permissions: List of permissions (user needs all)

    Returns:
        Dependency function
    """

    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        if not has_all_permissions(user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required (all): {[p.value for p in permissions]}",
            )
        return user

    return permission_checker


# ============================================================================
# DECORATOR-BASED PERMISSION CHECKERS (Alternative Pattern)
# ============================================================================


def require_permission_decorator(*permissions: Union[Permission, str]):
    """
    Decorator to require specific permissions for an endpoint.

    Usage:
        @router.post("/orders")
        @require_permission_decorator(Permission.CREATE_ORDER)
        async def create_order(current_user: User = Depends(get_current_active_user)):
            # ... endpoint logic

    Multiple Permissions (OR logic):
        @require_permission_decorator(Permission.VIEW_ALL_ORDERS, Permission.VIEW_OWN_ORDERS)
        # User needs EITHER permission

    Args:
        permissions: Required permissions (OR logic)

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
<<<<<<< HEAD
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
=======
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
                )

            # Get user permissions
            user_permissions = get_role_permissions(current_user.role)

            # Check if user has ANY of the required permissions (OR logic)
            has_any_perm = any(Permission(p) in user_permissions for p in permissions)

            if not has_any_perm:
                logger.warning(
                    f"Permission denied for user {current_user.email}. "
                    f"Required: {permissions}, Has: {user_permissions}",
<<<<<<< HEAD
                    extra={
                        "user_id": str(current_user.id),
                        "security_event": "permission_denied",
                    },
=======
                    extra={"user_id": str(current_user.id), "security_event": "permission_denied"},
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: "
                    f"{', '.join(str(p) for p in permissions)}",
                )

            # Execute endpoint
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions_decorator(*permissions: Permission):
    """
    Decorator to require ALL of the listed permissions (AND logic).

    Usage:
        @router.post("/admin/bulk-approve")
        @require_all_permissions_decorator(Permission.APPROVE_KYC, Permission.MANAGE_USERS)
        async def bulk_approve_kyc(current_user: User = Depends(get_current_active_user)):
            # User needs BOTH permissions

    Args:
        permissions: Required permissions (AND logic)

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
<<<<<<< HEAD
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
=======
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
                )

            user_permissions = get_role_permissions(current_user.role)

            # Check if user has ALL required permissions (AND logic)
            has_all_perms = all(p in user_permissions for p in permissions)

            if not has_all_perms:
                missing_permissions = [str(p) for p in permissions if p not in user_permissions]

                logger.warning(
                    f"Permission denied for user {current_user.email}. "
                    f"Missing: {missing_permissions}",
                    extra={"user_id": str(current_user.id)},
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing: {', '.join(missing_permissions)}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def admin_only_decorator():
    """
    Shortcut decorator for admin-only endpoints.

    Usage:
        @router.delete("/users/{user_id}")
        @admin_only_decorator()
        async def delete_user(user_id: str, current_user: User = Depends(get_current_active_user)):
            # Only admins can delete users

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
<<<<<<< HEAD
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
=======
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
                )

            if current_user.role != Role.ADMIN:
                logger.warning(
                    f"Admin-only endpoint accessed by non-admin: {current_user.email}",
                    extra={
                        "user_id": str(current_user.id),
                        "security_event": "unauthorized_admin_access",
                    },
                )

                raise HTTPException(
<<<<<<< HEAD
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required",
=======
                    status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# RESOURCE OWNERSHIP VERIFICATION
# ============================================================================


def verify_resource_ownership(
    user: User, resource_user_id: Optional[UUID], allow_admin: bool = True
) -> bool:
    """
    Verify user owns the resource.

    Args:
        user: Current user
        resource_user_id: User ID of resource owner
        allow_admin: If True, admins can access any resource

    Returns:
        True if user owns resource or is admin

    Raises:
        HTTPException 403: If user doesn't own resource
    """
    # Admin bypass
    if allow_admin and user.role == Role.ADMIN:
        return True

    # Check ownership
    if resource_user_id and str(user.id) != str(resource_user_id):
        logger.warning(
            f"Resource ownership violation: \n"
            f"User {user.email} tried to access resource owned by {resource_user_id}",
            extra={"user_id": str(user.id), "security_event": "ownership_violation"},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource",
        )

    return True


def verify_exporter_assignment(user: User, order_exporter_id: Optional[UUID]) -> bool:
    """
    Verify exporter is assigned to this order.

    Exporters can ONLY access orders assigned to them.
    Admins can access any order.

    Args:
        user: Current user (must be exporter or admin)
        order_exporter_id: Exporter ID assigned to order

    Returns:
        True if user is assigned or is admin

    Raises:
        HTTPException 403: If exporter not assigned
    """
    # Admin bypass
    if user.role == Role.ADMIN:
        return True

    # Verify exporter role
    if user.role != Role.EXPORTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Exporter access required"
        )

    # Check assignment
    if not order_exporter_id or str(user.id) != str(order_exporter_id):
        logger.warning(
            f"Exporter tried to access non-assigned order: {user.email}",
<<<<<<< HEAD
            extra={
                "user_id": str(user.id),
                "security_event": "unauthorized_exporter_access",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this order",
=======
            extra={"user_id": str(user.id), "security_event": "unauthorized_exporter_access"},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not assigned to this order"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
        )

    return True


def verify_clearing_agent_assignment(user: User, order_agent_id: Optional[UUID]) -> bool:
    """
    Verify clearing agent is assigned to this order.

    Args:
        user: Current user (must be agent or admin)
        order_agent_id: Agent ID assigned to order

    Returns:
        True if user is assigned or is admin

    Raises:
        HTTPException 403: If agent not assigned
    """
    # Admin bypass
    if user.role == Role.ADMIN:
        return True

    # Verify agent role
    if user.role != Role.CLEARING_AGENT:
        raise HTTPException(
<<<<<<< HEAD
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clearing agent access required",
=======
            status_code=status.HTTP_403_FORBIDDEN, detail="Clearing agent access required"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
        )

    # Check assignment
    if not order_agent_id or str(user.id) != str(order_agent_id):
        logger.warning(
            f"Clearing agent tried to access non-assigned order: {user.email}",
            extra={"user_id": str(user.id)},
        )

        raise HTTPException(
<<<<<<< HEAD
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this order",
=======
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not assigned to this order"
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
        )

    return True

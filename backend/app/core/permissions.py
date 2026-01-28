# backend/app/core/permissions.py

from enum import Enum
from typing import List, Callable
from functools import wraps
from fastapi import HTTPException, status, Depends

from app.modules.auth.models import Role, User
from .dependencies import get_current_active_user


class Permission(str, Enum):
    """All system permissions."""
    
    # Vehicle permissions
    VIEW_VEHICLES = "view_vehicles"
    MANAGE_VEHICLES = "manage_vehicles"
    
    # Order permissions
    CREATE_ORDER = "create_order"
    VIEW_OWN_ORDERS = "view_own_orders"
    VIEW_ALL_ORDERS = "view_all_orders"
    MANAGE_ORDERS = "manage_orders"
    CANCEL_OWN_ORDER = "cancel_own_order"
    
    # KYC permissions
    SUBMIT_KYC = "submit_kyc"
    VIEW_OWN_KYC = "view_own_kyc"
    REVIEW_KYC = "review_kyc"
    APPROVE_KYC = "approve_kyc"
    REJECT_KYC = "reject_kyc"
    
    # Payment permissions
    VIEW_OWN_PAYMENTS = "view_own_payments"
    VIEW_ALL_PAYMENTS = "view_all_payments"
    
    # Finance permissions
    REQUEST_FINANCE = "request_finance"
    VIEW_FINANCE_REQUESTS = "view_finance_requests"
    APPROVE_FINANCE = "approve_finance"
    REJECT_FINANCE = "reject_finance"
    
    # Insurance permissions
    REQUEST_INSURANCE = "request_insurance"
    APPROVE_INSURANCE = "approve_insurance"
    REJECT_INSURANCE = "reject_insurance"
    
    # LC permissions
    REQUEST_LC = "request_lc"
    APPROVE_LC = "approve_lc"
    REJECT_LC = "reject_lc"
    
    # Shipping/Exporter permissions
    VIEW_ASSIGNED_ORDERS = "view_assigned_orders"
    UPDATE_SHIPPING_DETAILS = "update_shipping_details"
    UPLOAD_SHIPMENT_DOCUMENTS = "upload_shipment_documents"
    MARK_ORDER_SHIPPED = "mark_order_shipped"
    ASSIGN_EXPORTER = "assign_exporter"
    APPROVE_SHIPMENT = "approve_shipment"
    VERIFY_SHIPPING_DOCS = "verify_shipping_docs"
    
    # Clearing agent permissions
    VIEW_CLEARANCE_TASKS = "view_clearance_tasks"
    MANAGE_CLEARANCE = "manage_clearance"
    UPLOAD_CUSTOMS_DOCUMENTS = "upload_customs_documents"
    UPDATE_SHIPMENT_STATUS = "update_shipment_status"
    ASSIGN_CLEARING_AGENT = "assign_clearing_agent"
    
    # User management
    VIEW_OWN_PROFILE = "view_own_profile"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    
    # Admin permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SYSTEM = "manage_system"
    MANAGE_TAX_RULES = "manage_tax_rules"
    APPROVE_TAX_RULES = "approve_tax_rules"
    OVERRIDE_STATUS = "override_status"
    
    # Security permissions
    MANAGE_SECURITY_EVENTS = "manage_security_events"
    VERIFY_FILE_INTEGRITY = "verify_file_integrity"
    
    # GDPR permissions
    EXPORT_OWN_DATA = "export_own_data"
    DELETE_OWN_DATA = "delete_own_data"
    
    # Document permissions
    UPLOAD_DOCUMENTS = "upload_documents"


# Role -> Permission mapping
ROLE_PERMISSIONS: dict[Role, List[Permission]] = {
    Role.CUSTOMER: [
        Permission.VIEW_VEHICLES,
        Permission.CREATE_ORDER,
        Permission.VIEW_OWN_ORDERS,
        Permission.CANCEL_OWN_ORDER,
        Permission.SUBMIT_KYC,
        Permission.VIEW_OWN_KYC,
        Permission.REQUEST_FINANCE,
        Permission.REQUEST_INSURANCE,
        Permission.VIEW_OWN_PROFILE,
        Permission.VIEW_OWN_PAYMENTS,
        Permission.EXPORT_OWN_DATA,
        Permission.DELETE_OWN_DATA,
        Permission.UPLOAD_DOCUMENTS,
    ],
    
    Role.ADMIN: [
        # Admins have ALL permissions
        *list(Permission)
    ],
    
    Role.CLEARING_AGENT: [
        Permission.VIEW_VEHICLES,
        Permission.VIEW_CLEARANCE_TASKS,
        Permission.MANAGE_CLEARANCE,
        Permission.UPLOAD_CUSTOMS_DOCUMENTS,
        Permission.UPDATE_SHIPMENT_STATUS,
        Permission.VIEW_OWN_PROFILE,
    ],
    
    Role.FINANCE_PARTNER: [
        Permission.VIEW_FINANCE_REQUESTS,
        Permission.APPROVE_FINANCE,
        Permission.REJECT_FINANCE,
        Permission.VIEW_OWN_PROFILE,
    ],
    
    Role.EXPORTER: [
        Permission.VIEW_ASSIGNED_ORDERS,
        Permission.UPDATE_SHIPPING_DETAILS,
        Permission.UPLOAD_SHIPMENT_DOCUMENTS,
        Permission.MARK_ORDER_SHIPPED,
        Permission.VIEW_OWN_PROFILE,
    ],
}


def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User object
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


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


def require_any_permission(permissions: List[Permission]):
    """
    Dependency to require ANY of the specified permissions.
    
    Args:
        permissions: List of permissions (user needs at least one)
        
    Returns:
        Dependency function
    """
    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        user_has_any = any(has_permission(user, perm) for perm in permissions)
        
        if not user_has_any:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required (any): {[p.value for p in permissions]}",
            )
        return user
    
    return permission_checker


def require_all_permissions(permissions: List[Permission]):
    """
    Dependency to require ALL of the specified permissions.
    
    Args:
        permissions: List of permissions (user needs all)
        
    Returns:
        Dependency function
    """
    async def permission_checker(user: User = Depends(get_current_active_user)) -> User:
        user_has_all = all(has_permission(user, perm) for perm in permissions)
        
        if not user_has_all:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required (all): {[p.value for p in permissions]}",
            )
        return user
    
    return permission_checker
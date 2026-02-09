/**
 * React hook for permission checking in components.
 */
import { useSelector } from "react-redux";
import { RootState } from "@/lib/store/store";

// Must match backend permissions
export enum Permission {
  // Vehicles
  VIEW_VEHICLES = "view_vehicles",
  MANAGE_VEHICLES = "manage_vehicles",

  // Orders
  CREATE_ORDER = "create_order",
  VIEW_OWN_ORDERS = "view_own_orders",
  VIEW_ALL_ORDERS = "view_all_orders",
  MANAGE_ORDERS = "manage_orders",

  // KYC
  SUBMIT_KYC = "submit_kyc",
  REVIEW_KYC = "review_kyc",
  APPROVE_KYC = "approve_kyc",

  // Admin
  MANAGE_USERS = "manage_users",

  // ... add all other permissions
}

// Role-permission mapping (must match backend)
const ROLE_PERMISSIONS: Record<string, Set<Permission>> = {
  CUSTOMER: new Set([
    Permission.VIEW_VEHICLES,
    Permission.CREATE_ORDER,
    Permission.VIEW_OWN_ORDERS,
    Permission.SUBMIT_KYC,
  ]),

  ADMIN: new Set(Object.values(Permission)), // All permissions

  EXPORTER: new Set([
    // ... exporter permissions
  ]),

  // ... other roles
};

const ROLE_ALIASES: Record<string, string> = {
  admin: "ADMIN",
  user: "CUSTOMER",
};

const normalizeRole = (role?: string): string | undefined => {
  if (!role) return undefined;
  return ROLE_ALIASES[role] ?? role.toUpperCase();
};

export function usePermission() {
  const { user } = useSelector((state: RootState) => state.auth);

  /**
   * Check if current user has a specific permission.
   */
  const hasPermission = (permission: Permission): boolean => {
    if (!user) return false;

    const roleKey = normalizeRole(user.role);
    const rolePermissions = (roleKey && ROLE_PERMISSIONS[roleKey]) || new Set();
    return rolePermissions.has(permission);
  };

  /**
   * Check if current user has ANY of the permissions.
   */
  const hasAnyPermission = (...permissions: Permission[]): boolean => {
    return permissions.some((p) => hasPermission(p));
  };

  /**
   * Check if current user has ALL of the permissions.
   */
  const hasAllPermissions = (...permissions: Permission[]): boolean => {
    return permissions.every((p) => hasPermission(p));
  };

  /**
   * Check if current user is admin.
   */
  const isAdmin = (): boolean => {
    return normalizeRole(user?.role) === "ADMIN";
  };

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin,
  };
}

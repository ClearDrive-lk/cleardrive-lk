"""
Test RBAC system.
"""
<<<<<<< HEAD

=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
import pytest
from app.core.permissions import (
    Permission,
    Role,
    get_role_permissions,
    has_permission,
    verify_resource_ownership,
)
from app.core.security import create_access_token
from app.modules.auth.models import User
from fastapi import HTTPException


class TestPermissionDefinitions:
    """Test permission definitions."""

    def test_all_permissions_defined(self):
        """Test all permissions are in enum."""
        # Should have 40+ permissions
        assert len(Permission) >= 40

    def test_permission_naming_convention(self):
        """Test permissions follow naming convention."""
        for perm in Permission:
            # Should be lowercase with underscores
            assert perm.value.islower()
            assert "_" in perm.value or perm.value in ["admin"]


class TestRolePermissions:
    """Test role-permission mappings."""

    def test_customer_permissions(self):
        """Test customer has correct permissions."""
        perms = get_role_permissions(Role.CUSTOMER)

        assert Permission.VIEW_VEHICLES in perms
        assert Permission.CREATE_ORDER in perms
        assert Permission.SUBMIT_KYC in perms

        # Should NOT have admin permissions
        assert Permission.MANAGE_USERS not in perms
        assert Permission.APPROVE_KYC not in perms

    def test_admin_has_all_permissions(self):
        """Test admin has ALL permissions."""
        admin_perms = get_role_permissions(Role.ADMIN)
        all_perms = set(Permission)

        assert admin_perms == all_perms

    def test_exporter_permissions(self):
        """Test exporter has shipping permissions only."""
        perms = get_role_permissions(Role.EXPORTER)

        assert Permission.VIEW_ASSIGNED_ORDERS in perms
        assert Permission.UPLOAD_SHIPMENT_DOCUMENTS in perms
        assert Permission.UPDATE_SHIPPING_DETAILS in perms

        # Should NOT have customer permissions
        assert Permission.CREATE_ORDER not in perms
        assert Permission.MAKE_PAYMENT not in perms

    def test_clearing_agent_permissions(self):
        """Test clearing agent has clearance permissions."""
        perms = get_role_permissions(Role.CLEARING_AGENT)

        assert Permission.VIEW_CLEARANCE_TASKS in perms
        assert Permission.MANAGE_CLEARANCE in perms
        assert Permission.UPLOAD_CUSTOMS_DOCUMENTS in perms

    def test_finance_partner_permissions(self):
        """Test finance partner has finance permissions."""
        perms = get_role_permissions(Role.FINANCE_PARTNER)

        assert Permission.VIEW_FINANCE_REQUESTS in perms
        assert Permission.APPROVE_FINANCE in perms
        assert Permission.REJECT_FINANCE in perms


class TestPermissionChecking:
    """Test permission checking logic."""

    def test_has_permission_customer(self):
        """Test customer permission check."""
        user = User(email="test@example.com", role=Role.CUSTOMER)

        assert has_permission(user, Permission.VIEW_VEHICLES) is True
        assert has_permission(user, Permission.MANAGE_USERS) is False

    def test_has_permission_admin(self):
        """Test admin has all permissions."""
        user = User(email="admin@example.com", role=Role.ADMIN)

        # Test random permissions
        assert has_permission(user, Permission.VIEW_VEHICLES) is True
        assert has_permission(user, Permission.MANAGE_USERS) is True
        assert has_permission(user, Permission.APPROVE_KYC) is True


class TestResourceOwnership:
    """Test resource ownership verification."""

    def test_owner_can_access_own_resource(self):
        """Test user can access their own resource."""
        user = User(id="user-123", email="test@example.com", role=Role.CUSTOMER)

        # Should not raise exception
        verify_resource_ownership(user, "user-123")

    def test_user_cannot_access_others_resource(self):
        """Test user cannot access other's resource."""
        user = User(id="user-123", email="test@example.com", role=Role.CUSTOMER)

        with pytest.raises(HTTPException) as exc:
            verify_resource_ownership(user, "user-456")

        assert exc.value.status_code == 403

    def test_admin_can_access_any_resource(self):
        """Test admin can access any resource."""
        admin = User(id="admin-123", email="admin@example.com", role=Role.ADMIN)

        # Should not raise exception
        verify_resource_ownership(admin, "user-456")


@pytest.mark.asyncio
class TestPermissionDecorators:
    """Test permission decorators on endpoints."""

    async def test_endpoint_with_permission(self, client, db):
        """Test accessing endpoint with correct permission."""
        # Create customer user
        user = User(email="test@example.com", role=Role.CUSTOMER)
        db.add(user)
        db.commit()

        # Create token
        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})

        # Access endpoint requiring VIEW_VEHICLES
        response = client.get("/api/v1/vehicles", headers={"Authorization": f"Bearer {token}"})

        # Should succeed (customer has VIEW_VEHICLES)
        assert response.status_code == 200

    async def test_endpoint_without_permission(self, client, db):
        """Test accessing endpoint without permission."""
        # Create customer user
        user = User(email="test@example.com", role=Role.CUSTOMER)
        db.add(user)
        db.commit()

        # Create token
        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})

        # Try to access admin-only endpoint (delete order)
        response = client.delete(
            "/api/v1/orders/dummy-id", headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail (customer doesn't have MANAGE_USERS)
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]


class TestPermissionMatrix:
    """Test complete permission matrix for all roles."""

    def test_permission_matrix(self):
        """Generate and verify complete permission matrix."""
        matrix = {}

        for role in Role:
            matrix[role.value] = {
                perm.value: perm in get_role_permissions(role) for perm in Permission
            }

        # Verify key permissions
        # CUSTOMER can create orders
        assert matrix["CUSTOMER"]["create_order"] is True

        # CUSTOMER cannot manage users
        assert matrix["CUSTOMER"]["manage_users"] is False

        # ADMIN can do everything
        for perm in Permission:
            assert matrix["ADMIN"][perm.value] is True

        # EXPORTER can upload shipment docs
        assert matrix["EXPORTER"]["upload_shipment_documents"] is True

        # EXPORTER cannot create orders
        assert matrix["EXPORTER"]["create_order"] is False

        print("\n=== PERMISSION MATRIX ===")
        print(f"{'Role':<20} | Customer | Admin | Exporter | Agent | Finance")
        print("-" * 80)

        for perm in Permission:
            row = f"{perm.value:<20} | "
            row += "✓" if matrix["CUSTOMER"][perm.value] else "✗"
            row += " " * 8 + "|"
            row += " ✓" if matrix["ADMIN"][perm.value] else " ✗"
            row += " " * 5 + "|"
            row += " ✓" if matrix["EXPORTER"][perm.value] else " ✗"
            row += " " * 7 + "|"
            row += " ✓" if matrix["CLEARING_AGENT"][perm.value] else " ✗"
            row += " " * 4 + "|"
            row += " ✓" if matrix["FINANCE_PARTNER"][perm.value] else " ✗"

            print(row)

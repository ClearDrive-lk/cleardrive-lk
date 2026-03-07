"""
Test admin user management.
"""

import pytest
from app.core.security import create_access_token
from app.modules.auth.models import Role, User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def admin_user(db: Session):
    """Create admin user for testing."""
    user = User(email="admin@test.com", name="Admin User", role=Role.ADMIN)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_user(db: Session):
    """Create customer user for testing."""
    user = User(email="customer@test.com", name="Customer User", role=Role.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Create admin access token."""
    return create_access_token(
        {"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value}
    )


@pytest.fixture
def customer_token(customer_user):
    """Create customer access token."""
    return create_access_token(
        {
            "sub": str(customer_user.id),
            "email": customer_user.email,
            "role": customer_user.role.value,
        }
    )


class TestGetUsers:
    """Test GET /api/v1/admin/users endpoint."""

    def test_get_users_as_admin(self, client: TestClient, admin_token: str, db: Session):
        """Test listing users as admin."""
        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert isinstance(data["users"], list)

    def test_get_users_with_search(self, client: TestClient, admin_token: str):
        """Test searching users."""
        response = client.get(
            "/api/v1/admin/users?search=admin", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should find admin user
        assert len(data["users"]) > 0
        assert any("admin" in user["email"].lower() for user in data["users"])

    def test_get_users_filter_by_role(self, client: TestClient, admin_token: str):
        """Test filtering by role."""
        response = client.get(
            "/api/v1/admin/users?role=ADMIN", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # All users should be admins
        assert all(user["role"] == "ADMIN" for user in data["users"])

    def test_get_users_pagination(self, client: TestClient, admin_token: str):
        """Test pagination."""
        response = client.get(
            "/api/v1/admin/users?page=1&limit=5", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["limit"] == 5
        assert len(data["users"]) <= 5

    def test_get_users_as_customer_fails(self, client: TestClient, customer_token: str):
        """Test that customers cannot list users."""
        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": f"Bearer {customer_token}"}
        )

        assert response.status_code == 403


class TestChangeUserRole:
    """Test PATCH /api/v1/admin/users/{id}/role endpoint."""

    def test_change_user_role(
        self, client: TestClient, admin_token: str, customer_user: User, db: Session
    ):
        """Test changing user role."""
        response = client.patch(
            f"/api/v1/admin/users/{customer_user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "EXPORTER",
                "reason": "User requested to become an exporter and has been verified",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["old_role"] == "CUSTOMER"
        assert data["new_role"] == "EXPORTER"
        assert data["user_id"] == str(customer_user.id)

        # Verify in database
        db.refresh(customer_user)
        assert customer_user.role == Role.EXPORTER

    def test_cannot_change_own_role(self, client: TestClient, admin_user: User, admin_token: str):
        """Test that admins cannot change their own role."""
        response = client.patch(
            f"/api/v1/admin/users/{admin_user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "CUSTOMER", "reason": "Testing self-demotion"},
        )

        assert response.status_code == 400
        assert "cannot change your own role" in response.json()["detail"].lower()

    def test_invalid_role(self, client: TestClient, admin_token: str, customer_user: User):
        """Test changing to invalid role."""
        response = client.patch(
            f"/api/v1/admin/users/{customer_user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "SUPER_ADMIN", "reason": "Testing invalid role"},
        )

        assert response.status_code == 400
        assert "invalid role" in response.json()["detail"].lower()

    def test_insufficient_reason(self, client: TestClient, admin_token: str, customer_user: User):
        """Test that reason is required and validated."""
        response = client.patch(
            f"/api/v1/admin/users/{customer_user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "ADMIN", "reason": "Test"},  # Too short
        )

        assert response.status_code == 400
        assert "reason" in response.json()["detail"].lower()

    def test_customer_cannot_change_roles(
        self, client: TestClient, customer_token: str, admin_user: User
    ):
        """Test that customers cannot change roles."""
        response = client.patch(
            f"/api/v1/admin/users/{admin_user.id}/role",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={"role": "CUSTOMER", "reason": "Trying to demote admin"},
        )

        assert response.status_code == 403


class TestRoleChangeSideEffects:
    """Test side effects for role changes."""

    def test_role_change_persists_updated_role(
        self,
        client: TestClient,
        admin_token: str,
        customer_user: User,
        db: Session,
    ):
        """Test that a successful role change is persisted in database."""
        response = client.patch(
            f"/api/v1/admin/users/{customer_user.id}/role",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "role": "ADMIN",
                "reason": "Promotion to admin",
            },
        )

        assert response.status_code == 200
        db.refresh(customer_user)
        assert customer_user.role == Role.ADMIN

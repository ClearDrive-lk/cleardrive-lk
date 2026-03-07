"""
Test admin dashboard analytics.
"""

import pytest
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import Role, User


@pytest.fixture
def sample_data(db):
    """Create sample data for testing."""
    # Create users
    for i in range(10):
        user = User(email=f"user{i}@test.com", name=f"User {i}", role=Role.CUSTOMER)
        db.add(user)

    db.commit()

    # Create orders
    users = db.query(User).all()
    for i, user in enumerate(users[:5]):
        order = Order(
            user_id=user.id,
            status=OrderStatus.DELIVERED if i % 2 == 0 else OrderStatus.PENDING,
            total_amount=10000 + (i * 1000),
        )
        db.add(order)

    db.commit()

    # Create payments
    orders = db.query(Order).all()
    for order in orders:
        payment = Payment(
            order_id=order.id,
            user_id=order.user_id,
            amount=order.total_amount,
            status=PaymentStatus.COMPLETED,
            payment_method="CARD",
        )
        db.add(payment)

    db.commit()


class TestDashboardStats:
    """Test GET /admin/dashboard/stats."""

    def test_get_stats(self, client, admin_token, sample_data):
        """Test getting dashboard stats."""
        response = client.get(
            "/api/v1/admin/dashboard/stats", headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_users" in data
        assert "total_orders" in data
        assert "total_revenue" in data
        assert data["total_users"] >= 10
        assert data["total_orders"] >= 5


class TestUserAnalytics:
    """Test GET /admin/dashboard/users."""

    def test_get_user_analytics(self, client, admin_token, sample_data):
        """Test getting user analytics."""
        response = client.get(
            "/api/v1/admin/dashboard/users?days=30",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "daily_registrations" in data
        assert "role_distribution" in data
        assert isinstance(data["daily_registrations"], list)

    def test_invalid_days_parameter(self, client, admin_token):
        """Test invalid days parameter."""
        response = client.get(
            "/api/v1/admin/dashboard/users?days=1000",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422  # Validation error


class TestOrderAnalytics:
    """Test GET /admin/dashboard/orders."""

    def test_get_order_analytics(self, client, admin_token, sample_data):
        """Test getting order analytics."""
        response = client.get(
            "/api/v1/admin/dashboard/orders?days=30",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "status_distribution" in data
        assert "daily_orders" in data
        assert "completion_rate" in data


class TestRevenueAnalytics:
    """Test GET /admin/dashboard/revenue."""

    def test_get_revenue_analytics(self, client, admin_token, sample_data):
        """Test getting revenue analytics."""
        response = client.get(
            "/api/v1/admin/dashboard/revenue?days=30",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "daily_revenue" in data
        assert "payment_method_breakdown" in data
        assert "revenue_growth_rate" in data


class TestPermissions:
    """Test permission enforcement."""

    def test_customer_cannot_access_dashboard(self, client, customer_token):
        """Test that customers cannot access dashboard."""
        response = client.get(
            "/api/v1/admin/dashboard/stats", headers={"Authorization": f"Bearer {customer_token}"}
        )

        assert response.status_code == 403

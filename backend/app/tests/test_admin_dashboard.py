"""
Test admin dashboard analytics.
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.modules.auth.models import Role, User
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.vehicles.models import Vehicle, VehicleStatus


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
    vehicles = []
    for i in range(5):
        vehicle = Vehicle(
            auction_id=f"AUC-{i}-{uuid4()}",
            stock_no=f"STK-{i}-{uuid4().hex[:8]}",
            make="Toyota",
            model="Prius",
            year=2020 + (i % 3),
            mileage=50000 + i * 1000,
            engine_cc=1500,
            fuel_type="PETROL",
            transmission="AUTO",
            drive_type="2WD",
            condition_grade="A",
            price_jpy=Decimal("1000000.00"),
            status=VehicleStatus.AVAILABLE,
            location="JP",
            source_url="https://example.com/vehicle",
        )
        db.add(vehicle)
        vehicles.append(vehicle)
    db.commit()

    for i, user in enumerate(users[:5]):
        order = Order(
            user_id=user.id,
            vehicle_id=vehicles[i].id,
            status=OrderStatus.DELIVERED if i % 2 == 0 else OrderStatus.CREATED,
            payment_status=OrderPaymentStatus.PENDING,
            shipping_address="No 12, Main Street, Colombo 05",
            phone="0771234567",
            total_cost_lkr=Decimal(10000 + (i * 1000)),
        )
        db.add(order)

    db.commit()

    # Create payments
    orders = db.query(Order).all()
    for order in orders:
        payment = Payment(
            order_id=order.id,
            user_id=order.user_id,
            idempotency_key=f"idem-{order.id}",
            amount=order.total_cost_lkr or Decimal("0.00"),
            currency="LKR",
            status=PaymentStatus.COMPLETED,
            payment_method="CARD",
        )
        db.add(payment)

    db.commit()


class TestDashboardStats:
    """Test GET /admin/dashboard/stats."""

    def test_get_stats(self, client, admin_headers, sample_data):
        """Test getting dashboard stats."""
        response = client.get("/api/v1/admin/dashboard/stats", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()

        assert "total_users" in data
        assert "total_orders" in data
        assert "total_revenue" in data
        assert data["total_users"] >= 10
        assert data["total_orders"] >= 5


class TestUserAnalytics:
    """Test GET /admin/dashboard/users."""

    def test_get_user_analytics(self, client, admin_headers, sample_data):
        """Test getting user analytics."""
        response = client.get(
            "/api/v1/admin/dashboard/users?days=30",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "daily_registrations" in data
        assert "role_distribution" in data
        assert isinstance(data["daily_registrations"], list)

    def test_invalid_days_parameter(self, client, admin_headers):
        """Test invalid days parameter."""
        response = client.get(
            "/api/v1/admin/dashboard/users?days=1000",
            headers=admin_headers,
        )

        assert response.status_code == 422  # Validation error


class TestOrderAnalytics:
    """Test GET /admin/dashboard/orders."""

    def test_get_order_analytics(self, client, admin_headers, sample_data):
        """Test getting order analytics."""
        response = client.get(
            "/api/v1/admin/dashboard/orders?days=30",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "status_distribution" in data
        assert "daily_orders" in data
        assert "completion_rate" in data


class TestRevenueAnalytics:
    """Test GET /admin/dashboard/revenue."""

    def test_get_revenue_analytics(self, client, admin_headers, sample_data):
        """Test getting revenue analytics."""
        response = client.get(
            "/api/v1/admin/dashboard/revenue?days=30",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "daily_revenue" in data
        assert "payment_method_breakdown" in data
        assert "revenue_growth_rate" in data


class TestPermissions:
    """Test permission enforcement."""

    def test_customer_cannot_access_dashboard(self, client, auth_headers):
        """Test that customers cannot access dashboard."""
        response = client.get("/api/v1/admin/dashboard/stats", headers=auth_headers)

        assert response.status_code == 403

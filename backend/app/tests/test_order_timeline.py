from __future__ import annotations

from decimal import Decimal

from app.core.security import create_access_token
from app.modules.auth.models import Role, User
from app.modules.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus,
)
from app.modules.vehicles.models import Vehicle, VehicleStatus


def _make_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


def _create_staff_user(db, *, email: str, role: Role) -> User:
    user = User(email=email, name=email.split("@")[0], role=role, google_id=f"google-{email}")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_vehicle(db, stock_no: str = "ORDER-TL-001") -> Vehicle:
    vehicle = Vehicle(
        stock_no=stock_no,
        make="Toyota",
        model="Prius",
        year=2020,
        price_jpy=Decimal("1500000.00"),
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def _create_order_with_history(db, user: User, vehicle: Vehicle) -> Order:
    order = Order(
        user_id=user.id,
        vehicle_id=vehicle.id,
        status=OrderStatus.CREATED,
        payment_status=PaymentStatus.PENDING,
        shipping_address="Encrypted Shipping Address",
        phone="0771234567",
        total_cost_lkr=Decimal("500000.00"),
    )
    db.add(order)
    db.flush()

    history = OrderStatusHistory(
        order_id=order.id,
        from_status=None,
        to_status=OrderStatus.CREATED,
        changed_by=user.id,
        notes="Order created by customer",
    )
    db.add(history)
    db.commit()
    db.refresh(order)
    return order


def test_timeline_returns_initial_created_event_for_owner(client, db, auth_headers, test_user):
    vehicle = _create_vehicle(db, stock_no="ORDER-TL-101")
    order = _create_order_with_history(db, test_user, vehicle)
    timeline_response = client.get(f"/api/v1/orders/{order.id}/timeline", headers=auth_headers)

    assert timeline_response.status_code == 200
    payload = timeline_response.json()
    assert payload["total_events"] == 1
    assert payload["timeline"][0]["from_status"] is None
    assert payload["timeline"][0]["to_status"] == "CREATED"
    assert payload["timeline"][0]["changed_by_id"] == str(test_user.id)
    assert payload["timeline"][0]["changed_by_email"] == test_user.email


def test_customer_cannot_view_another_customers_timeline(client, db, auth_headers, test_user):
    other_customer = _create_staff_user(db, email="other-customer@test.com", role=Role.CUSTOMER)
    vehicle = _create_vehicle(db, stock_no="ORDER-TL-102")
    order = _create_order_with_history(db, other_customer, vehicle)

    response = client.get(f"/api/v1/orders/{order.id}/timeline", headers=auth_headers)

    assert response.status_code == 403


def test_staff_role_can_view_customer_timeline(client, db, test_user):
    staff_user = _create_staff_user(db, email="finance-partner@test.com", role=Role.FINANCE_PARTNER)
    vehicle = _create_vehicle(db, stock_no="ORDER-TL-103")
    order = _create_order_with_history(db, test_user, vehicle)

    response = client.get(f"/api/v1/orders/{order.id}/timeline", headers=_make_headers(staff_user))

    assert response.status_code == 200
    assert response.json()["order_id"] == str(order.id)


def test_list_orders_returns_only_customer_orders_for_customer(client, db, auth_headers, test_user):
    own_vehicle = _create_vehicle(db, stock_no="ORDER-TL-105")
    other_vehicle = _create_vehicle(db, stock_no="ORDER-TL-106")
    other_customer = _create_staff_user(db, email="another-customer@test.com", role=Role.CUSTOMER)

    own_order = _create_order_with_history(db, test_user, own_vehicle)
    _create_order_with_history(db, other_customer, other_vehicle)

    response = client.get("/api/v1/orders", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [str(own_order.id)]


def test_timeline_returns_system_fallback_for_system_generated_history(
    client, db, auth_headers, test_user
):
    vehicle = _create_vehicle(db, stock_no="ORDER-TL-104")
    order = _create_order_with_history(db, test_user, vehicle)

    system_history = OrderStatusHistory(
        order_id=order.id,
        from_status=OrderStatus.CREATED,
        to_status=OrderStatus.PAYMENT_CONFIRMED,
        changed_by=None,
        notes="Payment completed by webhook",
    )
    db.add(system_history)
    db.commit()

    response = client.get(f"/api/v1/orders/{order.id}/timeline", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_events"] == 2
    assert payload["timeline"][1]["changed_by_id"] is None
    assert payload["timeline"][1]["changed_by_name"] == "System"
    assert payload["timeline"][1]["changed_by_email"] == "system@cleardrive.local"


def test_status_update_appends_to_timeline(client, db, auth_headers, test_user):
    vehicle = _create_vehicle(db, stock_no="ORDER-TL-201")
    order = _create_order_with_history(db, test_user, vehicle)

    admin_user = _create_staff_user(db, email="admin@test.com", role=Role.ADMIN)
    admin_headers = _make_headers(admin_user)

    # Precondition for PAYMENT_CONFIRMED
    order.payment_status = PaymentStatus.COMPLETED
    db.commit()

    update_response = client.patch(
        f"/api/v1/orders/{order.id}/status",
        params={"new_status": "PAYMENT_CONFIRMED", "notes": "Payment verified via test"},
        headers=admin_headers,
    )
    assert update_response.status_code == 200

    timeline_response = client.get(f"/api/v1/orders/{order.id}/timeline", headers=auth_headers)
    assert timeline_response.status_code == 200

    payload = timeline_response.json()
    assert payload["total_events"] == 2

    event_1 = payload["timeline"][0]
    event_2 = payload["timeline"][1]

    assert event_1["to_status"] == "CREATED"
    assert event_2["from_status"] == "CREATED"
    assert event_2["to_status"] == "PAYMENT_CONFIRMED"
    assert event_2["notes"] == "Payment verified via test"
    assert event_2["changed_by_id"] == str(admin_user.id)


def test_multiple_status_changes_tracked(client, db, auth_headers, test_user):
    from app.modules.shipping.models import ShipmentDetails

    vehicle = _create_vehicle(db, stock_no="ORDER-TL-202")
    order = _create_order_with_history(db, test_user, vehicle)

    admin_user = _create_staff_user(db, email="admin2@test.com", role=Role.ADMIN)
    admin_headers = _make_headers(admin_user)

    # 1st change to PAYMENT_CONFIRMED
    order.payment_status = PaymentStatus.COMPLETED
    db.commit()

    update_response = client.patch(
        f"/api/v1/orders/{order.id}/status",
        params={"new_status": "PAYMENT_CONFIRMED"},
        headers=admin_headers,
    )
    assert update_response.status_code == 200

    # 2nd change to ASSIGNED_TO_EXPORTER
    shipment = ShipmentDetails(order_id=order.id, exporter_id=admin_user.id)
    db.add(shipment)
    db.commit()

    update_response = client.patch(
        f"/api/v1/orders/{order.id}/status",
        params={"new_status": "ASSIGNED_TO_EXPORTER"},
        headers=admin_headers,
    )
    assert update_response.status_code == 200

    # 3rd change to CANCELLED (which is valid from ASSIGNED_TO_EXPORTER)
    update_response = client.patch(
        f"/api/v1/orders/{order.id}/status",
        params={"new_status": "CANCELLED"},
        headers=admin_headers,
    )
    assert update_response.status_code == 200

    timeline_response = client.get(f"/api/v1/orders/{order.id}/timeline", headers=auth_headers)
    payload = timeline_response.json()

    assert payload["total_events"] == 4
    assert payload["timeline"][-1]["to_status"] == "CANCELLED"
    assert payload["timeline"][-2]["to_status"] == "ASSIGNED_TO_EXPORTER"
    assert payload["timeline"][-3]["to_status"] == "PAYMENT_CONFIRMED"

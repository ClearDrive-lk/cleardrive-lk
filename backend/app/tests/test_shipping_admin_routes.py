from __future__ import annotations

from decimal import Decimal

from app.modules.auth.models import Role, User
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.shipping.models import ShipmentDetails
from app.modules.vehicles.models import Vehicle, VehicleStatus


def _create_paid_order_for_user(db, user: User, stock_no: str = "SHIP-001") -> Order:
    vehicle = Vehicle(
        stock_no=stock_no,
        make="Toyota",
        model="Corolla",
        year=2021,
        price_jpy=Decimal("1800000.00"),
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.flush()

    order = Order(
        user_id=user.id,
        vehicle_id=vehicle.id,
        status=OrderStatus.PAYMENT_CONFIRMED,
        payment_status=OrderPaymentStatus.COMPLETED,
        shipping_address="No 1, Galle Road, Colombo",
        phone="0771234567",
        total_cost_lkr=Decimal("650000.00"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _create_exporter(db, email: str = "exporter@test.com") -> User:
    exporter = User(
        email=email,
        name="Exporter User",
        role=Role.EXPORTER,
        google_id=f"google-{email}",
    )
    db.add(exporter)
    db.commit()
    db.refresh(exporter)
    return exporter


def test_assign_exporter_creates_shipment_updates_order_and_history(
    client, db, admin_headers, test_user, monkeypatch
):
    order = _create_paid_order_for_user(db, test_user, stock_no="SHIP-101")
    exporter = _create_exporter(db, "exporter-101@test.com")
    notification_calls: list[tuple[str, str]] = []

    async def _send_status_change_notification(order, old_status, new_status):
        notification_calls.append((old_status.value, new_status.value))

    monkeypatch.setattr(
        "app.modules.shipping.admin_routes.send_status_change_notification",
        _send_status_change_notification,
    )

    response = client.post(
        f"/api/v1/admin/shipping/{order.id}/assign",
        headers=admin_headers,
        json={"exporter_id": str(exporter.id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == str(order.id)
    assert body["assigned_exporter_id"] == str(exporter.id)

    shipment = db.query(ShipmentDetails).filter(ShipmentDetails.order_id == order.id).first()
    db.refresh(order)

    assert shipment is not None
    assert shipment.exporter_id == exporter.id
    assert order.status == OrderStatus.ASSIGNED_TO_EXPORTER

    history = (
        db.query(OrderStatusHistory)
        .filter(OrderStatusHistory.order_id == order.id)
        .order_by(OrderStatusHistory.created_at.desc())
        .first()
    )
    assert history is not None
    assert history.from_status == OrderStatus.PAYMENT_CONFIRMED
    assert history.to_status == OrderStatus.ASSIGNED_TO_EXPORTER
    assert notification_calls == [("PAYMENT_CONFIRMED", "ASSIGNED_TO_EXPORTER")]


def test_assign_exporter_requires_payment_confirmed_status(
    client, db, admin_headers, test_user, monkeypatch
):
    order = _create_paid_order_for_user(db, test_user, stock_no="SHIP-102")
    order.status = OrderStatus.CREATED
    db.commit()
    exporter = _create_exporter(db, "exporter-102@test.com")

    async def _send_status_change_notification(order, old_status, new_status):
        raise AssertionError("notification should not be called")

    monkeypatch.setattr(
        "app.modules.shipping.admin_routes.send_status_change_notification",
        _send_status_change_notification,
    )

    response = client.post(
        f"/api/v1/admin/shipping/{order.id}/assign",
        headers=admin_headers,
        json={"exporter_id": str(exporter.id)},
    )

    assert response.status_code == 400
    assert "PAYMENT_CONFIRMED" in response.json()["detail"]


def test_list_assignable_orders_returns_only_paid_unassigned_orders(
    client, db, admin_headers, test_user
):
    assignable_order = _create_paid_order_for_user(db, test_user, stock_no="SHIP-103")
    assigned_order = _create_paid_order_for_user(db, test_user, stock_no="SHIP-104")
    exporter = _create_exporter(db, "exporter-103@test.com")

    shipment = ShipmentDetails(order_id=assigned_order.id, exporter_id=exporter.id)
    db.add(shipment)
    db.commit()

    response = client.get("/api/v1/admin/shipping/assignable-orders", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [str(assignable_order.id)]
    assert payload[0]["status"] == "PAYMENT_CONFIRMED"
    assert payload[0]["payment_status"] == "COMPLETED"

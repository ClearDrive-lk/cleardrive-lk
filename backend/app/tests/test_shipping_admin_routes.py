from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

from app.modules.auth.models import Role, User
from app.modules.orders.models import Order, OrderStatus, OrderStatusHistory
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.shipping.models import (
    DocumentType,
    ShipmentDetails,
    ShipmentStatus,
    ShippingDocument,
)
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


def _create_shipment_ready_for_approval(
    db,
    user: User,
    *,
    stock_no: str = "SHIP-APPROVE-001",
) -> tuple[Order, ShipmentDetails, User]:
    order = _create_paid_order_for_user(db, user, stock_no=stock_no)
    exporter = _create_exporter(db, f"exporter-{stock_no.lower()}@test.com")

    shipment = ShipmentDetails(
        order_id=order.id,
        exporter_id=exporter.id,
        vessel_name="MV Horizon",
        vessel_registration="REG-909",
        voyage_number="VY-909",
        departure_port="Yokohama",
        arrival_port="Colombo",
        departure_date=date.today(),
        estimated_arrival_date=date.today() + timedelta(days=12),
        container_number="ABCU1234567",
        bill_of_landing_number="BOL-90909",
        seal_number="SL-909",
        tracking_number="TRK-909",
        documents_uploaded=True,
        submitted_at=datetime.utcnow(),
        status=ShipmentStatus.AWAITING_ADMIN_APPROVAL,
    )
    db.add(shipment)
    db.flush()

    for doc_type in (
        DocumentType.BILL_OF_LADING,
        DocumentType.COMMERCIAL_INVOICE,
        DocumentType.PACKING_LIST,
        DocumentType.EXPORT_CERTIFICATE,
    ):
        db.add(
            ShippingDocument(
                shipment_id=shipment.id,
                document_type=doc_type,
                file_url=f"https://example.com/{doc_type.value}.pdf",
                file_name=f"{doc_type.value}.pdf",
                file_size=1024,
                mime_type="application/pdf",
                sha256_hash="a" * 64,
                uploaded_by=exporter.id,
            )
        )

    order.status = OrderStatus.AWAITING_SHIPMENT_CONFIRMATION
    db.commit()
    db.refresh(order)
    db.refresh(shipment)
    return order, shipment, exporter


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
    assert payload[0]["customer_name"] == (test_user.name or test_user.email)
    assert payload[0]["customer_email"] == test_user.email
    assert payload[0]["vehicle_label"] == "Toyota Corolla (2021)"
    assert payload[0]["status"] == "PAYMENT_CONFIRMED"
    assert payload[0]["payment_status"] == "COMPLETED"
    assert payload[0]["total_cost_lkr"] == 650000.0


def test_get_pending_shipments_returns_ready_shipments_only(client, db, admin_headers, test_user):
    _, ready_shipment, _ = _create_shipment_ready_for_approval(db, test_user, stock_no="SHIP-201")

    exporter = _create_exporter(db, "exporter-ship-202@test.com")
    other_order = _create_paid_order_for_user(db, test_user, stock_no="SHIP-202")
    not_ready = ShipmentDetails(
        order_id=other_order.id,
        exporter_id=exporter.id,
        vessel_name="MV Pending",
        documents_uploaded=False,
        status=ShipmentStatus.PENDING_SHIPMENT,
    )
    db.add(not_ready)
    db.commit()

    response = client.get("/api/v1/admin/shipping/pending", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [str(ready_shipment.id)]
    assert payload[0]["order_id"] == str(ready_shipment.order_id)


def test_approve_shipment_marks_order_shipped_and_sends_notifications(
    client, db, admin_headers, test_user, monkeypatch
):
    order, shipment, exporter = _create_shipment_ready_for_approval(
        db, test_user, stock_no="SHIP-203"
    )
    customer_notification = AsyncMock()
    exporter_notification = AsyncMock(return_value="email-id")

    monkeypatch.setattr(
        "app.modules.shipping.admin_routes.send_status_change_notification",
        customer_notification,
    )
    monkeypatch.setattr(
        "app.modules.shipping.admin_routes.notification_service._enqueue_template",
        exporter_notification,
    )

    response = client.post(
        f"/api/v1/admin/shipping/{shipment.id}/approve",
        headers=admin_headers,
    )

    assert response.status_code == 200

    db.refresh(order)
    db.refresh(shipment)

    assert shipment.approved is True
    assert shipment.admin_approved_by is not None
    assert shipment.admin_approved_at is not None
    assert shipment.status == ShipmentStatus.CONFIRMED_SHIPPED
    assert order.status == OrderStatus.SHIPPED

    history = (
        db.query(OrderStatusHistory)
        .filter(OrderStatusHistory.order_id == order.id)
        .order_by(OrderStatusHistory.created_at.desc())
        .first()
    )
    assert history is not None
    assert history.from_status == OrderStatus.AWAITING_SHIPMENT_CONFIRMATION
    assert history.to_status == OrderStatus.SHIPPED

    customer_notification.assert_awaited_once()
    exporter_notification.assert_awaited_once()
    assert exporter_notification.await_args.kwargs["to_email"] == exporter.email

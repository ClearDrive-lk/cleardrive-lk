from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.core.security import create_access_token
from app.modules.auth.models import Role, User
from app.modules.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    PaymentStatus,
)
from app.modules.shipping.models import ShipmentDetails, ShipmentStatus
from app.modules.vehicles.models import Vehicle, VehicleStatus


def _exporter_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


def _create_exporter(db, email: str) -> User:
    exporter = User(email=email, name="Exporter", role=Role.EXPORTER, google_id=f"gid-{email}")
    db.add(exporter)
    db.commit()
    db.refresh(exporter)
    return exporter


def _create_assigned_order(db, exporter: User, stock_no: str) -> tuple[Order, ShipmentDetails]:
    vehicle = Vehicle(
        stock_no=stock_no,
        make="Toyota",
        model="Corolla",
        year=2020,
        price_jpy=Decimal("2000000.00"),
        status=VehicleStatus.AVAILABLE,
    )
    customer = User(
        email=f"customer-{stock_no}@test.com",
        name="Customer",
        role=Role.CUSTOMER,
        google_id=f"gid-customer-{stock_no}",
    )
    db.add(vehicle)
    db.add(customer)
    db.flush()

    order = Order(
        user_id=customer.id,
        vehicle_id=vehicle.id,
        status=OrderStatus.ASSIGNED_TO_EXPORTER,
        payment_status=PaymentStatus.COMPLETED,
        shipping_address="Colombo",
        phone="0771234567",
        total_cost_lkr=Decimal("500000.00"),
    )
    db.add(order)
    db.flush()

    shipment = ShipmentDetails(order_id=order.id, exporter_id=exporter.id)
    db.add(shipment)
    db.commit()
    db.refresh(order)
    db.refresh(shipment)
    return order, shipment


def test_submit_shipping_details_updates_shipment_and_order(client, db):
    exporter = _create_exporter(db, "exp-cd71-1@test.com")
    headers = _exporter_headers(exporter)
    order, shipment = _create_assigned_order(db, exporter, "CD71-001")

    departure = date.today()
    arrival = departure + timedelta(days=10)

    response = client.post(
        f"/api/v1/shipping/{order.id}/details",
        headers=headers,
        json={
            "vessel_name": "MV Horizon",
            "vessel_registration": "REG-771",
            "voyage_number": "VY-101",
            "departure_port": "Yokohama",
            "arrival_port": "Colombo",
            "departure_date": departure.isoformat(),
            "estimated_arrival_date": arrival.isoformat(),
            "container_number": "ABCU1234567",
            "bill_of_landing_number": "BOL-77889",
            "seal_number": "SL-100",
            "tracking_number": "TRK-001",
        },
    )

    assert response.status_code == 200
    db.refresh(order)
    db.refresh(shipment)
    assert shipment.vessel_name == "MV Horizon"
    assert shipment.vessel_registration == "REG-771"
    assert shipment.departure_port == "Yokohama"
    assert shipment.arrival_port == "Colombo"
    assert shipment.departure_date == departure
    assert shipment.estimated_arrival_date == arrival
    assert shipment.container_number == "ABCU1234567"
    assert shipment.bill_of_landing_number == "BOL-77889"
    assert shipment.status == ShipmentStatus.AWAITING_ADMIN_APPROVAL
    assert order.status == OrderStatus.AWAITING_SHIPMENT_CONFIRMATION

    history = (
        db.query(OrderStatusHistory)
        .filter(OrderStatusHistory.order_id == order.id)
        .order_by(OrderStatusHistory.created_at.desc())
        .first()
    )
    assert history is not None
    assert history.from_status == OrderStatus.ASSIGNED_TO_EXPORTER
    assert history.to_status == OrderStatus.AWAITING_SHIPMENT_CONFIRMATION


def test_submit_shipping_details_rejects_non_owner_exporter(client, db):
    assigned_exporter = _create_exporter(db, "exp-cd71-owner@test.com")
    other_exporter = _create_exporter(db, "exp-cd71-other@test.com")
    headers = _exporter_headers(other_exporter)
    order, _ = _create_assigned_order(db, assigned_exporter, "CD71-002")

    departure = date.today()
    arrival = departure + timedelta(days=7)

    response = client.post(
        f"/api/v1/shipping/{order.id}/details",
        headers=headers,
        json={
            "vessel_name": "MV Pacific",
            "vessel_registration": "REG-990",
            "voyage_number": "VY-202",
            "departure_port": "Tokyo",
            "arrival_port": "Colombo",
            "departure_date": departure.isoformat(),
            "estimated_arrival_date": arrival.isoformat(),
            "container_number": "MSCU1234567",
            "bill_of_landing_number": "BOL-20202",
            "seal_number": "SL-202",
            "tracking_number": "TRK-202",
        },
    )

    assert response.status_code == 403


def test_submit_shipping_details_validates_arrival_after_departure(client, db):
    exporter = _create_exporter(db, "exp-cd71-3@test.com")
    headers = _exporter_headers(exporter)
    order, _ = _create_assigned_order(db, exporter, "CD71-003")

    departure = date.today()
    arrival = departure - timedelta(days=1)

    response = client.post(
        f"/api/v1/shipping/{order.id}/details",
        headers=headers,
        json={
            "vessel_name": "MV Invalid",
            "vessel_registration": "REG-123",
            "voyage_number": "VY-303",
            "departure_port": "Tokyo",
            "arrival_port": "Colombo",
            "departure_date": departure.isoformat(),
            "estimated_arrival_date": arrival.isoformat(),
            "container_number": "OOLU1234567",
            "bill_of_landing_number": "BOL-30303",
            "seal_number": "SL-303",
            "tracking_number": "TRK-303",
        },
    )

    assert response.status_code == 422

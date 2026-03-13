from __future__ import annotations

from decimal import Decimal

from app.core.security import create_access_token
from app.modules.auth.models import Role, User
from app.modules.orders.models import Order, OrderStatus, PaymentStatus
from app.modules.shipping.models import DocumentType, ShipmentDetails, ShippingDocument
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


def test_upload_shipping_document_detects_mime_from_file_bytes(client, db, mocker):
    exporter = _create_exporter(db, "exp-cd72-mime@test.com")
    headers = _exporter_headers(exporter)
    order, _shipment = _create_assigned_order(db, exporter, "CD72-MIME")

    upload_mock = mocker.patch(
        "app.modules.shipping.routes.storage.upload_file",
        new=mocker.AsyncMock(return_value={"url": "https://files.example/shipping/doc.pdf"}),
    )
    integrity_mock = mocker.patch(
        "app.modules.shipping.routes.file_integrity_service.create_integrity_record"
    )

    response = client.post(
        f"/api/v1/shipping/{order.id}/documents",
        headers=headers,
        data={"document_type": "BILL_OF_LADING"},
        files={"file": ("fake.pdf", b"not-a-pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
    upload_mock.assert_not_called()
    integrity_mock.assert_not_called()


def test_upload_shipping_document_stores_sha256_hash(client, db, mocker):
    exporter = _create_exporter(db, "exp-cd72-hash@test.com")
    headers = _exporter_headers(exporter)
    order, shipment = _create_assigned_order(db, exporter, "CD72-HASH")

    mocker.patch(
        "app.modules.shipping.routes.storage.upload_file",
        new=mocker.AsyncMock(return_value={"url": "https://files.example/shipping/bol.pdf"}),
    )
    integrity_mock = mocker.patch(
        "app.modules.shipping.routes.file_integrity_service.create_integrity_record"
    )

    response = client.post(
        f"/api/v1/shipping/{order.id}/documents",
        headers=headers,
        data={"document_type": "BILL_OF_LADING"},
        files={"file": ("bol.pdf", b"%PDF-1.4 test payload", "application/octet-stream")},
    )

    assert response.status_code == 201
    db.refresh(shipment)
    document = (
        db.query(ShippingDocument)
        .filter(
            ShippingDocument.shipment_id == shipment.id,
            ShippingDocument.document_type == DocumentType.BILL_OF_LADING,
        )
        .one()
    )
    assert document.sha256_hash
    assert len(document.sha256_hash) == 64
    integrity_mock.assert_called_once()


def test_container_photos_allow_multiple_uploads_and_listing(client, db, mocker):
    exporter = _create_exporter(db, "exp-cd72-photos@test.com")
    headers = _exporter_headers(exporter)
    order, shipment = _create_assigned_order(db, exporter, "CD72-PHOTOS")

    async def _upload_file(*, bucket, file_path, file_content, content_type):
        return {"url": f"https://files.example/{file_path}"}

    mocker.patch(
        "app.modules.shipping.routes.storage.upload_file",
        side_effect=_upload_file,
    )
    mocker.patch("app.modules.shipping.routes.file_integrity_service.create_integrity_record")

    first = client.post(
        f"/api/v1/shipping/{order.id}/documents",
        headers=headers,
        data={"document_type": "CONTAINER_PHOTO"},
        files={"file": ("photo-1.jpg", b"\xff\xd8\xffphoto1", "image/jpeg")},
    )
    second = client.post(
        f"/api/v1/shipping/{order.id}/documents",
        headers=headers,
        data={"document_type": "CONTAINER_PHOTO"},
        files={"file": ("photo-2.jpg", b"\xff\xd8\xffphoto2", "image/jpeg")},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    docs = (
        db.query(ShippingDocument)
        .filter(
            ShippingDocument.shipment_id == shipment.id,
            ShippingDocument.document_type == DocumentType.CONTAINER_PHOTO,
        )
        .all()
    )
    assert len(docs) == 2

    list_response = client.get(
        f"/api/v1/shipping/{order.id}/documents",
        headers=headers,
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    photo_names = [doc["file_name"] for doc in payload if doc["document_type"] == "CONTAINER_PHOTO"]
    assert photo_names == ["photo-1.jpg", "photo-2.jpg"]

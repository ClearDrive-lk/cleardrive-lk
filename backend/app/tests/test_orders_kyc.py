from uuid import uuid4

from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.vehicles.models import Vehicle, VehicleStatus


def _create_vehicle(db, stock_no: str = "KYC-ORDER-001") -> Vehicle:
    vehicle = Vehicle(
        stock_no=stock_no,
        make="Toyota",
        model="Raize",
        year=2025,
        price_jpy=1500000,
        status=VehicleStatus.AVAILABLE,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def _create_kyc(db, user_id, status: KYCStatus) -> KYCDocument:
    kyc = KYCDocument(
        user_id=user_id,
        nic_front_url="https://example.com/nic-front.jpg",
        nic_back_url="https://example.com/nic-back.jpg",
        selfie_url="https://example.com/selfie.jpg",
        status=status,
    )
    db.add(kyc)
    db.commit()
    db.refresh(kyc)
    return kyc


def test_create_order_requires_approved_kyc(client, auth_headers, db, test_user):
    vehicle = _create_vehicle(db, stock_no=f"KYC-ORDER-{uuid4().hex[:8]}")
    _create_kyc(db, test_user.id, KYCStatus.PENDING)

    response = client.post(
        "/api/v1/orders",
        headers=auth_headers,
        json={
            "vehicle_id": str(vehicle.id),
            "shipping_address": "123 Main Street, Colombo 03",
            "phone": "0771234567",
        },
    )

    assert response.status_code == 400
    assert "Only APPROVED users can create orders." in response.json()["detail"]

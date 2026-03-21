from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import Session as UserSession
from app.modules.gdpr.models import GDPRDeletion, GDPRDeletionStatus
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.orders.models import Order, OrderStatus
from app.modules.orders.models import PaymentStatus as OrderPaymentStatus
from app.modules.vehicles.models import Vehicle


def _create_vehicle(db) -> Vehicle:
    vehicle = Vehicle(
        stock_no="GDPR-TEST-001",
        make="Toyota",
        model="Vitz",
        year=2020,
        price_jpy=Decimal("1000000.00"),
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


def test_gdpr_delete_requires_exact_confirmation(client, auth_headers):
    response = client.delete("/api/v1/gdpr/delete?confirmation=DELETE")
    assert response.status_code == 401

    response = client.delete(
        "/api/v1/gdpr/delete?confirmation=DELETE",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "DELETE MY ACCOUNT" in response.json()["detail"]


def test_gdpr_delete_is_blocked_by_active_orders(client, db, test_user, auth_headers):
    vehicle = _create_vehicle(db)
    db.add(
        Order(
            user_id=test_user.id,
            vehicle_id=vehicle.id,
            status=OrderStatus.CREATED,
            payment_status=OrderPaymentStatus.PENDING,
            shipping_address="encrypted-address",
            phone="0771234567",
        )
    )
    db.commit()

    response = client.delete(
        "/api/v1/gdpr/delete?confirmation=DELETE%20MY%20ACCOUNT",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "active order" in response.json()["detail"].lower()

    deletion = db.query(GDPRDeletion).filter(GDPRDeletion.user_id == test_user.id).first()
    assert deletion is not None
    assert deletion.status == GDPRDeletionStatus.REJECTED

    audit_events = {
        item.event_type
        for item in db.query(AuditLog).filter(AuditLog.user_id == test_user.id).all()
    }
    assert AuditEventType.GDPR_DELETION_REQUESTED in audit_events
    assert AuditEventType.GDPR_DELETION_REJECTED in audit_events


def test_gdpr_delete_success_anonymizes_and_revokes_sessions(
    client, db, test_user, auth_headers, mocker
):
    mocker.patch("app.services.gdpr.data_deletion_service.storage.delete_file", new=AsyncMock())
    mocker.patch(
        "app.services.gdpr.data_deletion_service.get_user_sessions",
        new=AsyncMock(return_value=[{"token_jti": "refresh-jti-1"}]),
    )
    mocker.patch("app.services.gdpr.data_deletion_service.blacklist_token", new=AsyncMock())
    mocker.patch(
        "app.services.gdpr.data_deletion_service.delete_all_user_sessions", new=AsyncMock()
    )

    vehicle = _create_vehicle(db)
    db.add(
        Order(
            user_id=test_user.id,
            vehicle_id=vehicle.id,
            status=OrderStatus.DELIVERED,
            payment_status=OrderPaymentStatus.COMPLETED,
            shipping_address="encrypted-address",
            phone="0771234567",
        )
    )
    db.add(
        KYCDocument(
            user_id=test_user.id,
            nic_front_url="https://test.supabase.co/storage/v1/object/public/kyc-documents/user/nic_front.jpg",
            nic_back_url="https://test.supabase.co/storage/v1/object/public/kyc-documents/user/nic_back.jpg",
            selfie_url="https://test.supabase.co/storage/v1/object/public/kyc-documents/user/selfie.jpg",
            nic_number="199912312345",
            full_name="Test User",
            status=KYCStatus.PENDING,
            user_provided_data={"full_name": "Test User"},
            extracted_data={"front": {"name": "Test User"}},
            discrepancies={"name_mismatch": False},
        )
    )
    db.add(
        UserSession(
            user_id=test_user.id,
            refresh_token_hash="hash",
            is_active=True,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    )
    db.commit()

    response = client.delete(
        "/api/v1/gdpr/delete?confirmation=DELETE%20MY%20ACCOUNT",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["details"]["data_anonymized"] is True
    assert payload["details"]["sessions_revoked"] is True

    db.refresh(test_user)
    assert test_user.email.startswith("deleted_")
    assert test_user.deleted_at is not None
    assert test_user.phone is None
    assert test_user.google_id is None

    kyc = db.query(KYCDocument).filter(KYCDocument.user_id == test_user.id).first()
    assert kyc is not None
    assert kyc.nic_front_url == ""
    assert kyc.nic_back_url == ""
    assert kyc.selfie_url == ""
    assert kyc.extracted_data is None

    order = db.query(Order).filter(Order.user_id == test_user.id).first()
    assert order is not None
    assert order.phone == "0000000000"
    assert order.shipping_address != "encrypted-address"

    db_session = db.query(UserSession).filter(UserSession.user_id == test_user.id).first()
    assert db_session is not None
    assert db_session.is_active is False

    deletion = db.query(GDPRDeletion).filter(GDPRDeletion.user_id == test_user.id).first()
    assert deletion is not None
    assert deletion.status == GDPRDeletionStatus.COMPLETED

    audit_events = {
        item.event_type
        for item in db.query(AuditLog).filter(AuditLog.user_id == test_user.id).all()
    }
    assert AuditEventType.GDPR_DELETION_REQUESTED in audit_events
    assert AuditEventType.GDPR_DELETION_COMPLETED in audit_events

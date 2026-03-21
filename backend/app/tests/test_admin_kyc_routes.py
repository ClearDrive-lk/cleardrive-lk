from __future__ import annotations

from datetime import date

from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import User
from app.modules.kyc.models import KYCDocument, KYCStatus


def _create_kyc_document(
    db,
    user: User,
    *,
    status: KYCStatus = KYCStatus.PENDING,
    extracted_data: dict | None = None,
) -> KYCDocument:
    kyc = KYCDocument(
        user_id=user.id,
        nic_number="200012345678",
        full_name="Test User",
        date_of_birth=date(2000, 1, 15),
        address="No 1, Galle Road, Colombo",
        gender="M",
        nic_front_url="https://example.com/front.jpg",
        nic_back_url="https://example.com/back.jpg",
        selfie_url="https://example.com/selfie.jpg",
        user_provided_data={
            "nic_number": "200012345678",
            "full_name": "Test User",
            "date_of_birth": "2000-01-15",
            "address": "No 1, Galle Road, Colombo",
            "gender": "M",
        },
        extracted_data=extracted_data
        or {
            "front": {
                "nic_number": "200012345678",
                "full_name": "Test User",
                "date_of_birth": "2000-01-15",
            },
            "back": {
                "address": "No 1, Galle Road, Colombo",
                "gender": "M",
            },
            "extraction_method": "vps_ollama",
        },
        status=status,
    )
    db.add(kyc)
    db.commit()
    db.refresh(kyc)
    return kyc


def test_get_pending_kyc_documents_returns_review_queue(client, db, admin_headers, test_user):
    pending = _create_kyc_document(db, test_user)

    manual_user = User(
        email="manual@example.com",
        name="Manual Review User",
        role=test_user.role,
        google_id="manual-review-user",
    )
    db.add(manual_user)
    db.commit()
    db.refresh(manual_user)
    _create_kyc_document(
        db,
        manual_user,
        status=KYCStatus.PENDING_MANUAL_REVIEW,
        extracted_data={"extraction_method": "manual_review_required"},
    )

    response = client.get("/api/v1/admin/kyc/pending", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["id"] == str(pending.id)
    assert payload[0]["user_email"] == test_user.email
    assert payload[0]["auto_extracted"] is True
    assert payload[1]["needs_manual_extraction"] is True


def test_get_kyc_detail_includes_comparison_rows(client, db, admin_headers, test_user):
    kyc = _create_kyc_document(
        db,
        test_user,
        extracted_data={
            "front": {
                "nic_number": "999999999999",
                "full_name": "Mismatch Name",
                "date_of_birth": "2000-01-15",
            },
            "back": {"address": "Elsewhere", "gender": "F"},
            "extraction_method": "vps_ollama",
        },
    )

    response = client.get(f"/api/v1/admin/kyc/{kyc.id}", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_email"] == test_user.email
    assert payload["discrepancies"]["nic_number"] is True
    assert any(row["matches"] is False for row in payload["comparison_rows"])


def test_extract_manual_kyc_data_updates_payload_and_status(client, db, admin_headers, test_user):
    kyc = _create_kyc_document(
        db,
        test_user,
        status=KYCStatus.PENDING_MANUAL_REVIEW,
        extracted_data={"extraction_method": "manual_review_required"},
    )

    response = client.post(
        f"/api/v1/admin/kyc/{kyc.id}/extract-manual",
        headers=admin_headers,
        json={
            "nic_number": "200099999999",
            "full_name": "Manual Review Name",
            "date_of_birth": "2000-02-03",
            "address": "Manual Address",
            "gender": "F",
            "issue_date": "2024-01-15",
        },
    )

    assert response.status_code == 200
    db.refresh(kyc)
    assert kyc.status == KYCStatus.PENDING
    assert kyc.extracted_data["extraction_method"] == "manual"
    assert kyc.extracted_data["front"]["full_name"] == "Manual Review Name"
    assert kyc.extracted_data["back"]["issue_date"] == "2024-01-15"
    assert response.json()["needs_manual_extraction"] is False
    assert response.json()["manual_extracted_by"] == "admin@example.com"


def test_approve_kyc_updates_status_creates_audit_and_sends_email(
    client, db, admin_headers, admin_user, test_user, monkeypatch
):
    kyc = _create_kyc_document(db, test_user)
    sent_emails: list[tuple[str, str]] = []

    async def _send_kyc_approved(email, user_name):
        sent_emails.append((email, "KYC Approved - ClearDrive.lk"))
        return "mock_id"

    monkeypatch.setattr(
        "app.modules.kyc.admin_routes.notification_service.send_kyc_approved", _send_kyc_approved
    )

    response = client.post(f"/api/v1/admin/kyc/{kyc.id}/approve", headers=admin_headers)

    assert response.status_code == 200
    db.refresh(kyc)
    assert kyc.status == KYCStatus.APPROVED
    assert kyc.reviewed_by == admin_user.id
    assert sent_emails == [(test_user.email, "KYC Approved - ClearDrive.lk")]

    audit = db.query(AuditLog).filter(AuditLog.user_id == test_user.id).first()
    assert audit is not None
    assert audit.event_type == AuditEventType.KYC_APPROVED


def test_reject_kyc_requires_reason_and_sends_email(
    client, db, admin_headers, admin_user, test_user, monkeypatch
):
    kyc = _create_kyc_document(db, test_user)
    kyc.nic_front_url = (
        "https://example.supabase.co/storage/v1/object/public/kyc-documents/user-1/front.jpg"
    )
    kyc.nic_back_url = (
        "https://example.supabase.co/storage/v1/object/public/kyc-documents/user-1/back.jpg"
    )
    kyc.selfie_url = (
        "https://example.supabase.co/storage/v1/object/public/kyc-documents/user-1/selfie.jpg"
    )
    db.commit()
    sent_emails: list[tuple[str, str]] = []
    deleted_paths: list[tuple[str, str]] = []

    async def _send_kyc_rejected(email, user_name, rejection_reason):
        sent_emails.append((email, "KYC Rejected - ClearDrive.lk"))
        return "mock_id"

    async def _delete_file(bucket, file_path):
        deleted_paths.append((bucket, file_path))
        return True

    monkeypatch.setattr(
        "app.modules.kyc.admin_routes.notification_service.send_kyc_rejected", _send_kyc_rejected
    )
    monkeypatch.setattr("app.modules.kyc.admin_routes.storage.delete_file", _delete_file)

    short_reason_response = client.post(
        f"/api/v1/admin/kyc/{kyc.id}/reject",
        headers=admin_headers,
        json={"reason": "too short"},
    )
    assert short_reason_response.status_code == 422

    response = client.post(
        f"/api/v1/admin/kyc/{kyc.id}/reject",
        headers=admin_headers,
        json={"reason": "NIC images are blurry and unreadable"},
    )

    assert response.status_code == 200
    db.refresh(kyc)
    assert kyc.status == KYCStatus.REJECTED
    assert kyc.reviewed_by == admin_user.id
    assert kyc.rejection_reason == "NIC images are blurry and unreadable"
    assert sent_emails == [(test_user.email, "KYC Rejected - ClearDrive.lk")]
    assert deleted_paths == [
        ("kyc-documents", "user-1/front.jpg"),
        ("kyc-documents", "user-1/back.jpg"),
        ("kyc-documents", "user-1/selfie.jpg"),
    ]

    audit = db.query(AuditLog).filter(AuditLog.user_id == test_user.id).first()
    assert audit is not None
    assert audit.event_type == AuditEventType.KYC_REJECTED

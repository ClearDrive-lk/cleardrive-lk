from __future__ import annotations

from app.modules.security.models import (
    FileIntegrity,
    SecurityEvent,
    SecurityEventType,
    VerificationStatus,
)


def _create_integrity_record(db, admin_user, **overrides) -> FileIntegrity:
    payload = {
        "file_url": "https://test.supabase.co/storage/v1/object/public/kyc-documents/user-1/nic_front.jpg",
        "file_name": "nic_front.jpg",
        "file_size": 128,
        "mime_type": "image/jpeg",
        "sha256_hash": "3aa105fb448a8a0f05d1e281e0c43174de7b6d3ef13da69866d9659117f2bdcb",  # pragma: allowlist secret
        "uploaded_by": admin_user.id,
        "verification_status": VerificationStatus.PENDING,
    }
    payload.update(overrides)
    record = FileIntegrity(**payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_verify_file_integrity_endpoint_marks_verified(
    client, db, admin_headers, admin_user, monkeypatch
):
    record = _create_integrity_record(db, admin_user)

    async def _download_file(bucket: str, file_path: str) -> bytes:
        assert bucket == "kyc-documents"
        assert file_path == "user-1/nic_front.jpg"
        return b"trusted-file"

    monkeypatch.setattr("app.core.storage.storage.download_file", _download_file)

    response = client.post(f"/api/v1/security/verify-file/{record.id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["is_valid"] is True
    db.refresh(record)
    assert record.verification_status == VerificationStatus.VERIFIED
    assert record.verification_error is None
    assert record.tampering_detected is False


def test_verify_file_integrity_endpoint_detects_tampering(
    client, db, admin_headers, admin_user, monkeypatch
):
    record = _create_integrity_record(db, admin_user)
    sent_emails: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.services.security.file_integrity.settings.ADMIN_EMAILS", "admin@cleardrive.lk"
    )

    async def _download_file(bucket: str, file_path: str) -> bytes:
        return b"tampered-file"

    async def _send_email(to_email, subject, html_content, text_content):
        sent_emails.append((to_email, subject))
        return True

    monkeypatch.setattr("app.core.storage.storage.download_file", _download_file)
    monkeypatch.setattr("app.services.security.file_integrity.send_email", _send_email)

    response = client.post(f"/api/v1/security/verify-file/{record.id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["is_valid"] is False
    db.refresh(record)
    assert record.verification_status == VerificationStatus.TAMPERED
    assert record.tampering_detected is True
    assert "Hash mismatch" in (record.verification_error or "")
    assert sent_emails == [
        ("admin@cleardrive.lk", "[Security] File tampering detected: nic_front.jpg")
    ]

    event = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.event_type == SecurityEventType.FILE_TAMPERING)
        .first()
    )
    assert event is not None
    assert event.details["file_integrity_id"] == str(record.id)


def test_verify_all_files_returns_statistics(client, db, admin_headers, admin_user, monkeypatch):
    verified = _create_integrity_record(
        db,
        admin_user,
        file_url="https://test.supabase.co/storage/v1/object/public/kyc-documents/user-1/good.jpg",
        file_name="good.jpg",
        sha256_hash="b3c222c8051922e68d78d594e96fca7ced5d0722bcbf7762d7729ca5dcb6a200",  # pragma: allowlist secret
    )
    tampered = _create_integrity_record(
        db,
        admin_user,
        file_url="https://test.supabase.co/storage/v1/object/public/kyc-documents/user-1/bad.jpg",
        file_name="bad.jpg",
        sha256_hash="3aa105fb448a8a0f05d1e281e0c43174de7b6d3ef13da69866d9659117f2bdcb",  # pragma: allowlist secret
    )

    async def _download_file(bucket: str, file_path: str) -> bytes:
        if file_path == "user-1/good.jpg":
            return b"good-file"
        return b"tampered-file"

    async def _send_email(to_email, subject, html_content, text_content):
        return True

    monkeypatch.setattr(
        "app.services.security.file_integrity.settings.ADMIN_EMAILS", "admin@cleardrive.lk"
    )
    monkeypatch.setattr("app.core.storage.storage.download_file", _download_file)
    monkeypatch.setattr("app.services.security.file_integrity.send_email", _send_email)

    response = client.post("/api/v1/security/verify-all-files", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()["statistics"]
    assert payload["total"] == 2
    assert payload["valid"] == 1
    assert payload["invalid"] == 1
    assert payload["errors"] == 0
    assert payload["tampering_detected"][0]["file_name"] == "bad.jpg"
    db.refresh(verified)
    db.refresh(tampered)
    assert verified.verification_status == VerificationStatus.VERIFIED
    assert tampered.verification_status == VerificationStatus.TAMPERED


def test_get_tampering_alerts_returns_detected_records(client, db, admin_headers, admin_user):
    record = _create_integrity_record(
        db,
        admin_user,
        tampering_detected=True,
        verification_status=VerificationStatus.TAMPERED,
        verification_error="Hash mismatch - file may have been tampered with",
    )

    response = client.get("/api/v1/security/tampering-alerts", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_alerts"] == 1
    assert payload["alerts"][0]["id"] == str(record.id)
    assert payload["alerts"][0]["verification_error"] == record.verification_error

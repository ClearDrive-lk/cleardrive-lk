from __future__ import annotations

from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.security.models import FileIntegrity


def test_upload_kyc_persists_user_provided_payload(client, db, auth_headers, monkeypatch):
    async def _upload_file(*, bucket, file_path, file_content, content_type, upsert=False):
        assert upsert is True
        return {"url": f"https://example.com/{file_path}"}

    async def _extract_nic_with_retry(file_content, side, content_type, max_retries=1):
        if side == "front":
            return {
                "nic_number": "200012345678",
                "full_name": "OCR Name",
                "date_of_birth": "2000-01-15",
            }
        return {"address": "OCR Address", "gender": "M"}

    monkeypatch.setattr("app.modules.kyc.routes.storage.upload_file", _upload_file)
    monkeypatch.setattr("app.modules.kyc.routes.extract_nic_with_retry", _extract_nic_with_retry)

    files = {
        "nic_front": ("front.jpg", b"\xff\xd8\xff\xdbfront", "image/jpeg"),
        "nic_back": ("back.jpg", b"\xff\xd8\xff\xdbback", "image/jpeg"),
        "selfie": ("selfie.jpg", b"\xff\xd8\xff\xdbselfie", "image/jpeg"),
    }
    data = {
        "nic_number": "199912345678",
        "full_name": "Submitted Name",
        "date_of_birth": "1999-04-05",
        "address": "Submitted Address",
        "gender": "F",
    }

    response = client.post("/api/v1/kyc/upload", headers=auth_headers, files=files, data=data)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == KYCStatus.PENDING.value

    kyc = db.query(KYCDocument).first()
    assert kyc is not None
    assert kyc.user_provided_data == data
    assert kyc.nic_number == "199912345678"
    assert kyc.full_name == "Submitted Name"
    assert str(kyc.date_of_birth) == "1999-04-05"
    assert kyc.address == "Submitted Address"
    assert kyc.gender == "F"


def test_upload_kyc_allows_resubmission_after_rejection(
    client, db, auth_headers, test_user, monkeypatch
):
    rejected = KYCDocument(
        user_id=test_user.id,
        nic_number="old-nic",
        full_name="Old Name",
        nic_front_url="https://example.com/old-front.jpg",
        nic_back_url="https://example.com/old-back.jpg",
        selfie_url="https://example.com/old-selfie.jpg",
        user_provided_data={"nic_number": "old-nic"},
        status=KYCStatus.REJECTED,
        rejection_reason="Not extracted",
    )
    db.add(rejected)
    db.commit()
    db.refresh(rejected)

    async def _upload_file(*, bucket, file_path, file_content, content_type, upsert=False):
        assert upsert is True
        return {"url": f"https://example.com/{file_path}"}

    async def _extract_nic_with_retry(file_content, side, content_type, max_retries=1):
        if side == "front":
            return {
                "nic_number": "200012345678",
                "full_name": "OCR Name",
                "date_of_birth": "2000-01-15",
            }
        return {"address": "OCR Address", "gender": "M", "issue_date": "2020-01-01"}

    monkeypatch.setattr("app.modules.kyc.routes.storage.upload_file", _upload_file)
    monkeypatch.setattr("app.modules.kyc.routes.extract_nic_with_retry", _extract_nic_with_retry)

    files = {
        "nic_front": ("front.jpg", b"\xff\xd8\xff\xdbfront", "image/jpeg"),
        "nic_back": ("back.jpg", b"\xff\xd8\xff\xdbback", "image/jpeg"),
        "selfie": ("selfie.jpg", b"\xff\xd8\xff\xdbselfie", "image/jpeg"),
    }
    data = {
        "nic_number": "20023457891233",
        "full_name": "WALGAMA KANKANAMGE YASINDU MALITH DE SILVA",
        "date_of_birth": "2002-11-07",
        "address": "THILINA TEMPLE ROAD THALPE",
        "gender": "MALE",
    }

    response = client.post("/api/v1/kyc/upload", headers=auth_headers, files=files, data=data)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == KYCStatus.PENDING.value

    rows = db.query(KYCDocument).all()
    assert len(rows) == 1
    db.refresh(rejected)
    assert rejected.status == KYCStatus.PENDING
    assert rejected.rejection_reason is None
    assert rejected.user_provided_data == data
    assert rejected.extracted_data is not None


def test_upload_kyc_reuses_existing_file_integrity_rows_on_resubmission(
    client, db, auth_headers, test_user, monkeypatch
):
    rejected = KYCDocument(
        user_id=test_user.id,
        nic_number="old-nic",
        full_name="Old Name",
        nic_front_url="https://example.com/old-front.jpg",
        nic_back_url="https://example.com/old-back.jpg",
        selfie_url="https://example.com/old-selfie.jpg",
        user_provided_data={"nic_number": "old-nic"},
        status=KYCStatus.REJECTED,
        rejection_reason="Not extracted",
    )
    db.add(rejected)
    db.add(
        FileIntegrity(
            file_url=f"https://example.com/{test_user.id}/nic_front.jpg",
            file_name="nic_front.jpg",
            file_size=1,
            mime_type="image/jpeg",
            sha256_hash="old",
            uploaded_by=str(test_user.id),
        )
    )
    db.add(
        FileIntegrity(
            file_url=f"https://example.com/{test_user.id}/nic_back.jpg",
            file_name="nic_back.jpg",
            file_size=1,
            mime_type="image/jpeg",
            sha256_hash="old",
            uploaded_by=str(test_user.id),
        )
    )
    db.add(
        FileIntegrity(
            file_url=f"https://example.com/{test_user.id}/selfie.jpg",
            file_name="selfie.jpg",
            file_size=1,
            mime_type="image/jpeg",
            sha256_hash="old",
            uploaded_by=str(test_user.id),
        )
    )
    db.commit()

    async def _upload_file(*, bucket, file_path, file_content, content_type, upsert=False):
        return {"url": f"https://example.com/{file_path}"}

    async def _extract_nic_with_retry(file_content, side, content_type, max_retries=1):
        if side == "front":
            return {
                "nic_number": "200012345678",
                "full_name": "OCR Name",
                "date_of_birth": "2000-01-15",
            }
        return {"address": "OCR Address", "gender": "M", "issue_date": "2020-01-01"}

    monkeypatch.setattr("app.modules.kyc.routes.storage.upload_file", _upload_file)
    monkeypatch.setattr("app.modules.kyc.routes.extract_nic_with_retry", _extract_nic_with_retry)

    files = {
        "nic_front": ("front.jpg", b"\xff\xd8\xff\xdbfront", "image/jpeg"),
        "nic_back": ("back.jpg", b"\xff\xd8\xff\xdbback", "image/jpeg"),
        "selfie": ("selfie.jpg", b"\xff\xd8\xff\xdbselfie", "image/jpeg"),
    }
    data = {
        "nic_number": "20023457891233",
        "full_name": "WALGAMA KANKANAMGE YASINDU MALITH DE SILVA",
        "date_of_birth": "2002-11-07",
        "address": "THILINA TEMPLE ROAD THALPE",
        "gender": "MALE",
    }

    response = client.post("/api/v1/kyc/upload", headers=auth_headers, files=files, data=data)

    assert response.status_code == 200
    assert db.query(FileIntegrity).count() == 3

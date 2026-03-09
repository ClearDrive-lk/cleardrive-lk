from __future__ import annotations

from app.modules.kyc.models import KYCDocument, KYCStatus


def test_upload_kyc_persists_user_provided_payload(client, db, auth_headers, monkeypatch):
    async def _upload_file(*, bucket, file_path, file_content, content_type):
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

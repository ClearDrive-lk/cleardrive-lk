"""Tests for CD-24 gazette extraction upload pipeline."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import AsyncMock

from app.models.gazette import Gazette


def test_upload_gazette_success(client, admin_headers, mocker):
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(
            return_value={
                "text": "Gazette text",
                "tables": [{"headers": ["Vehicle Type"], "rows": [{"Vehicle Type": "SEDAN"}]}],
                "pages": 2,
                "confidence": 0.94,
            }
        ),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(
            return_value={
                "gazette_no": "2024/01",
                "effective_date": "2024-02-01",
                "rules": [
                    {
                        "vehicle_type": "SEDAN",
                        "fuel_type": "PETROL",
                        "engine_min": 1000,
                        "engine_max": 1500,
                        "customs_percent": 25.0,
                        "excise_percent": 50.0,
                        "vat_percent": 15.0,
                        "pal_percent": 7.5,
                        "cess_percent": 0.0,
                        "apply_on": "CIF_PLUS_CUSTOMS",
                        "notes": "standard",
                    }
                ],
            }
        ),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/01"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["rules_count"] == 1
    assert data["confidence"] == 0.94
    assert data["preview"]["gazette_no"] == "2024/01"


def test_upload_gazette_requires_admin(client, auth_headers):
    response = client.post(
        "/api/v1/gazette/upload",
        headers=auth_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/NOADMIN"},
    )
    assert response.status_code == 403


def test_upload_gazette_rejects_non_pdf(client, admin_headers):
    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.txt", BytesIO(b"not pdf"), "text/plain")},
        data={"gazette_no": "2024/TXT"},
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]


def test_upload_gazette_size_limit(client, admin_headers, mocker):
    mocker.patch("app.modules.gazette.routes.settings.MAX_GAZETTE_SIZE_MB", 0)
    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/LARGE"},
    )
    assert response.status_code == 413


def test_upload_gazette_fallback_manual_review(client, admin_headers, db, mocker):
    mocker.patch(
        "app.modules.gazette.routes.document_ai_service.parse_gazette_pdf",
        new=AsyncMock(return_value={"text": "raw", "tables": [], "pages": 1, "confidence": 0.61}),
    )
    mocker.patch(
        "app.modules.gazette.routes.gemini_service.structure_gazette",
        new=AsyncMock(side_effect=RuntimeError("invalid json")),
    )

    response = client.post(
        "/api/v1/gazette/upload",
        headers=admin_headers,
        files={"file": ("gazette.pdf", BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        data={"gazette_no": "2024/FALLBACK"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NEEDS_MANUAL_REVIEW"
    assert data["rules_count"] == 0
    assert "message" in data

    saved = db.query(Gazette).filter(Gazette.gazette_no == "2024/FALLBACK").first()
    assert saved is not None
    assert saved.status == "PENDING"

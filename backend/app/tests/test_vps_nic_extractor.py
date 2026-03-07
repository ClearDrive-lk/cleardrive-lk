from __future__ import annotations

from io import BytesIO
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from PIL import Image
from vps_nic_extractor import main as vps_main


def _valid_png_bytes() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (2, 2), color=(255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


def test_extract_nic_requires_internal_secret(monkeypatch):
    monkeypatch.setattr(vps_main, "INTERNAL_SECRET", "test-secret")

    with TestClient(vps_main.app) as client:
        response = client.post(
            "/extract/nic",
            files={"image": ("nic.png", _valid_png_bytes(), "image/png")},
            headers={"X-Side": "front"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid secret"


def test_extract_nic_smoke_success_schema(monkeypatch, mocker):
    monkeypatch.setattr(vps_main, "INTERNAL_SECRET", "test-secret")
    mocker.patch(
        "vps_nic_extractor.main._extract_with_ollama",
        new=AsyncMock(
            return_value={
                "nic_number": "200012345678",
                "full_name": "Test User",
                "date_of_birth": "2000-01-15",
                "confidence": 0.85,
                "side": "front",
            }
        ),
    )

    with TestClient(vps_main.app) as client:
        response = client.post(
            "/extract/nic",
            files={"image": ("nic.png", _valid_png_bytes(), "image/png")},
            headers={
                "X-Internal-Secret": "test-secret",  # pragma: allowlist secret
                "X-Side": "front",
            },  # pragma: allowlist secret
        )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"nic_number", "full_name", "date_of_birth", "confidence", "side"}
    assert payload["side"] == "front"
    assert isinstance(payload["confidence"], float)
    assert payload["nic_number"] == "200012345678"


def test_extract_nic_schema_failure_returns_500(monkeypatch, mocker):
    monkeypatch.setattr(vps_main, "INTERNAL_SECRET", "test-secret")
    mocker.patch(
        "vps_nic_extractor.main._extract_with_ollama",
        new=AsyncMock(side_effect=RuntimeError("Schema validation failed")),
    )

    with TestClient(vps_main.app) as client:
        response = client.post(
            "/extract/nic",
            files={"image": ("nic.png", _valid_png_bytes(), "image/png")},
            headers={
                "X-Internal-Secret": "test-secret",  # pragma: allowlist secret
                "X-Side": "front",
            },
        )

    assert response.status_code == 500
    assert "Extraction failed" in response.json()["detail"]

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("PIL")
from vps_nic_extractor import main as vps_main


def _valid_png_bytes() -> bytes:
    # 1x1 transparent PNG to avoid requiring Pillow in test environments.
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc`\x00\x02"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )


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


@pytest.mark.asyncio
async def test_extract_with_ollama_tolerates_empty_back_fields(monkeypatch, mocker):
    class _MockResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"response": '{"address":"Test Address","gender":"","issue_date":""}'}

    post_mock = AsyncMock(return_value=_MockResponse())
    mock_client = mocker.MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = post_mock

    mocker.patch("vps_nic_extractor.main.httpx.AsyncClient", return_value=mock_client)
    monkeypatch.setattr(vps_main, "OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.setattr(vps_main, "OLLAMA_MODEL", "minicpm-v:latest")

    payload = await vps_main._extract_with_ollama(_valid_png_bytes(), "back")

    assert payload["address"] == "Test Address"
    assert payload["gender"] == ""
    assert payload["issue_date"] == ""
    assert payload["side"] == "back"
    assert payload["confidence"] == 0.85

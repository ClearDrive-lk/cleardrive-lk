from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
from app.services import vps_proxy
from app.services.vps_proxy import VPSConnectionError, VPSExtractionError


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_extract_nic_from_vps_success(mocker, monkeypatch):
    monkeypatch.setattr(vps_proxy.settings, "VPS_URL", "http://127.0.0.1:8001")
    monkeypatch.setattr(vps_proxy.settings, "VPS_SECRET", "secret")
    monkeypatch.setattr(vps_proxy.settings, "KYC_VPS_TIMEOUT_SECONDS", 60.0)

    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        200,
        {
            "nic_number": "200012345678",
            "full_name": "Test User",
            "date_of_birth": "2000-01-15",
        },
    )
    cm = AsyncMock()
    cm.__aenter__.return_value = client
    mocker.patch("app.services.vps_proxy.httpx.AsyncClient", return_value=cm)

    result = await vps_proxy.extract_nic_from_vps(b"image-bytes", side="front")
    assert result["nic_number"] == "200012345678"
    client.post.assert_called_once()


@pytest.mark.asyncio
async def test_extract_nic_from_vps_non_200_raises(mocker, monkeypatch):
    monkeypatch.setattr(vps_proxy.settings, "VPS_URL", "http://127.0.0.1:8001")
    monkeypatch.setattr(vps_proxy.settings, "VPS_SECRET", "secret")

    client = AsyncMock()
    client.post.return_value = _FakeResponse(500, text="internal-error")
    cm = AsyncMock()
    cm.__aenter__.return_value = client
    mocker.patch("app.services.vps_proxy.httpx.AsyncClient", return_value=cm)

    with pytest.raises(VPSExtractionError):
        await vps_proxy.extract_nic_from_vps(b"image-bytes", side="front")


@pytest.mark.asyncio
async def test_extract_nic_from_vps_timeout_raises(mocker, monkeypatch):
    monkeypatch.setattr(vps_proxy.settings, "VPS_URL", "http://127.0.0.1:8001")
    monkeypatch.setattr(vps_proxy.settings, "VPS_SECRET", "secret")

    client = AsyncMock()
    client.post.side_effect = httpx.TimeoutException("timeout")
    cm = AsyncMock()
    cm.__aenter__.return_value = client
    mocker.patch("app.services.vps_proxy.httpx.AsyncClient", return_value=cm)

    with pytest.raises(VPSConnectionError):
        await vps_proxy.extract_nic_from_vps(b"image-bytes", side="front")


@pytest.mark.asyncio
async def test_extract_nic_from_vps_invalid_json_raises(mocker, monkeypatch):
    monkeypatch.setattr(vps_proxy.settings, "VPS_URL", "http://127.0.0.1:8001")
    monkeypatch.setattr(vps_proxy.settings, "VPS_SECRET", "secret")

    client = AsyncMock()
    response = _FakeResponse(200)
    response.json = lambda: (_ for _ in ()).throw(ValueError("invalid json"))  # type: ignore[method-assign]
    client.post.return_value = response
    cm = AsyncMock()
    cm.__aenter__.return_value = client
    mocker.patch("app.services.vps_proxy.httpx.AsyncClient", return_value=cm)

    with pytest.raises(VPSExtractionError, match="Invalid JSON response from VPS"):
        await vps_proxy.extract_nic_from_vps(b"image-bytes", side="front")


@pytest.mark.asyncio
async def test_extract_nic_with_retry_retries_then_succeeds(mocker):
    extract_mock = mocker.patch(
        "app.services.vps_proxy.extract_nic_from_vps",
        new=AsyncMock(
            side_effect=[
                VPSConnectionError("temporary"),
                {"nic_number": "200012345678"},
            ]
        ),
    )
    sleep_mock = mocker.patch("app.services.vps_proxy.asyncio.sleep", new=AsyncMock())

    result = await vps_proxy.extract_nic_with_retry(b"image-bytes", side="front", max_retries=1)
    assert result == {"nic_number": "200012345678"}
    assert extract_mock.await_count == 2
    sleep_mock.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_extract_nic_with_retry_returns_none_after_failures(mocker):
    extract_mock = mocker.patch(
        "app.services.vps_proxy.extract_nic_from_vps",
        new=AsyncMock(side_effect=VPSConnectionError("down")),
    )
    sleep_mock = mocker.patch("app.services.vps_proxy.asyncio.sleep", new=AsyncMock())

    result = await vps_proxy.extract_nic_with_retry(b"image-bytes", side="back", max_retries=1)
    assert result is None
    assert extract_mock.await_count == 2
    sleep_mock.assert_awaited_once_with(1)

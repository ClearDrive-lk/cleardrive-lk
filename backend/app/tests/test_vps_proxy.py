"""
Tests for VPS NIC extraction proxy service.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest
from app.services.vps_proxy import (
    VPSConnectionError,
    VPSExtractionError,
    extract_nic_from_vps,
    extract_nic_with_retry,
)


@pytest.mark.asyncio
async def test_extract_nic_from_vps_success(mocker):
    mocker.patch("app.services.vps_proxy.settings.VPS_URL", "https://vps.test")
    mocker.patch("app.services.vps_proxy.settings.VPS_SECRET", "secret")
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "nic_number": "200012345678",
        "full_name": "John Doe",
    }
    mock_post.return_value = mock_response

    result = await extract_nic_from_vps(b"fake_image_bytes")

    assert result["nic_number"] == "200012345678"
    assert result["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_extract_nic_from_vps_timeout(mocker):
    mocker.patch("app.services.vps_proxy.settings.VPS_URL", "https://vps.test")
    mocker.patch("app.services.vps_proxy.settings.VPS_SECRET", "secret")
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_post.side_effect = httpx.TimeoutException("Timeout")

    with pytest.raises(VPSConnectionError, match="VPS timeout"):
        await extract_nic_from_vps(b"fake_image_bytes")


@pytest.mark.asyncio
async def test_extract_nic_from_vps_invalid_json(mocker):
    mocker.patch("app.services.vps_proxy.settings.VPS_URL", "https://vps.test")
    mocker.patch("app.services.vps_proxy.settings.VPS_SECRET", "secret")
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("invalid json")
    mock_post.return_value = mock_response

    with pytest.raises(VPSExtractionError, match="Invalid JSON response from VPS"):
        await extract_nic_from_vps(b"fake_image_bytes")


@pytest.mark.asyncio
async def test_extract_nic_with_retry_succeeds_after_retry(mocker):
    mock_extract = mocker.patch(
        "app.services.vps_proxy.extract_nic_from_vps", new_callable=AsyncMock
    )
    mock_sleep = mocker.patch("app.services.vps_proxy.asyncio.sleep", new_callable=AsyncMock)
    mock_extract.side_effect = [
        VPSConnectionError("First attempt failed"),
        {"nic_number": "200012345678"},
    ]

    result = await extract_nic_with_retry(b"fake_bytes", max_retries=1)

    assert result == {"nic_number": "200012345678"}
    assert mock_extract.call_count == 2
    mock_sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_extract_nic_with_retry_returns_none_when_all_attempts_fail(mocker):
    mock_extract = mocker.patch(
        "app.services.vps_proxy.extract_nic_from_vps", new_callable=AsyncMock
    )
    mock_extract.side_effect = VPSExtractionError("bad image")

    result = await extract_nic_with_retry(b"fake_bytes", max_retries=1)

    assert result is None
    assert mock_extract.call_count == 2

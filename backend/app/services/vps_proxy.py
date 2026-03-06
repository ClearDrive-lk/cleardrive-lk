"""
VPS proxy service for NIC extraction (CD-50.8/9/10).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class VPSConnectionError(Exception):
    """Raised when the VPS is unreachable or times out."""


class VPSExtractionError(Exception):
    """Raised when the VPS returns an extraction failure."""


def _vps_base_url() -> str:
    if not settings.VPS_URL:
        raise VPSConnectionError("VPS_URL is not configured")
    return settings.VPS_URL.rstrip("/")


def _vps_secret() -> str:
    if not settings.VPS_SECRET:
        raise VPSConnectionError("VPS_SECRET is not configured")
    return settings.VPS_SECRET


async def extract_nic_from_vps(
    image_bytes: bytes,
    *,
    side: str = "front",
    content_type: str = "image/jpeg",
) -> dict[str, Any]:
    """
    Extract NIC details from private VPS.

    Uses a 60-second timeout by default (configurable via settings).
    """
    url = f"{_vps_base_url()}/extract/nic"
    headers = {
        "X-Internal-Secret": _vps_secret(),
        "X-Side": side,
    }
    files = {"image": (f"nic_{side}.jpg", image_bytes, content_type)}

    try:
        async with httpx.AsyncClient(timeout=settings.KYC_VPS_TIMEOUT_SECONDS) as client:
            response = await client.post(url, files=files, headers=headers)

        if response.status_code != 200:
            detail = response.text[:500]
            raise VPSExtractionError(f"VPS returned {response.status_code}: {detail}")

        payload = response.json()
        if not isinstance(payload, dict):
            raise VPSExtractionError("Invalid VPS response payload")
        if payload.get("error"):
            raise VPSExtractionError(str(payload["error"]))

        return payload
    except httpx.TimeoutException as exc:
        raise VPSConnectionError(f"VPS timeout after {settings.KYC_VPS_TIMEOUT_SECONDS}s") from exc
    except httpx.ConnectError as exc:
        raise VPSConnectionError("VPS unreachable") from exc
    except httpx.HTTPError as exc:
        raise VPSExtractionError(f"VPS HTTP error: {exc}") from exc
    except ValueError as exc:
        raise VPSExtractionError("Invalid JSON response from VPS") from exc
    except Exception as exc:
        raise VPSExtractionError(f"VPS extraction failed: {exc}") from exc


async def extract_nic_with_retry(
    image_bytes: bytes,
    *,
    side: str = "front",
    content_type: str = "image/jpeg",
    max_retries: int | None = None,
) -> dict[str, Any] | None:
    """
    Extract NIC data with exponential backoff retry.

    Returns None if all attempts fail.
    """
    retries = settings.KYC_VPS_MAX_RETRIES if max_retries is None else max_retries
    total_attempts = max(0, retries) + 1

    for attempt in range(total_attempts):
        try:
            return await extract_nic_from_vps(image_bytes, side=side, content_type=content_type)
        except (VPSConnectionError, VPSExtractionError) as exc:
            if attempt == total_attempts - 1:
                logger.warning("VPS extraction failed for side=%s after retries: %s", side, exc)
                return None
            backoff_seconds = 2**attempt
            logger.warning(
                "VPS extraction failed for side=%s (attempt %s/%s): %s. Retrying in %ss",
                side,
                attempt + 1,
                total_attempts,
                exc,
                backoff_seconds,
            )
            await asyncio.sleep(backoff_seconds)

    return None


async def check_vps_health() -> bool:
    """Check if VPS is reachable and responding."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{_vps_base_url()}/health",
                headers={"X-Internal-Secret": _vps_secret()},
            )
        return response.status_code == 200
    except Exception:
        return False

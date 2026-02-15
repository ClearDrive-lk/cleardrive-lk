"""
Redis client and OTP storage utilities.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional, cast

import redis.asyncio as redis  # type: ignore[import-untyped]

from .config import settings

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance (singleton).

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    await get_redis()


# ---------------------------------------------------------------------------
# OTP Storage
# ---------------------------------------------------------------------------


async def store_otp(email: str, otp: str, expiry_minutes: int = 5) -> bool:
    """
    Store OTP in Redis with expiry.

    Redis Key : otp:{email}
    Value (JSON):
        {
            "otp": "123456",
            "created_at": "2026-01-23T10:30:00",
            "attempts": 0
        }
    """
    client = await get_redis()
    key = f"otp:{email}"

    value = json.dumps(
        {
            "otp": otp,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
        }
    )

    await client.setex(key, timedelta(minutes=expiry_minutes), value)
    return True


async def get_otp(email: str) -> Optional[dict]:
    """Retrieve OTP data from Redis. Returns None if the key has expired or never existed."""
    client = await get_redis()
    value = await client.get(f"otp:{email}")

    if not value:
        return None

    return cast(Optional[dict], json.loads(value))


async def delete_otp(email: str) -> bool:
    """Delete OTP from Redis (one-time use)."""
    client = await get_redis()
    await client.delete(f"otp:{email}")
    return True


async def increment_otp_attempts(email: str) -> int:
    """
    Increment failed OTP verification attempts.
    Deletes the OTP once OTP_MAX_ATTEMPTS is reached.

    Returns:
        Current attempt count (0 if the key no longer exists).
    """
    client = await get_redis()
    key = f"otp:{email}"

    data = await get_otp(email)
    if not data:
        return 0

    data["attempts"] += 1

    if data["attempts"] >= settings.OTP_MAX_ATTEMPTS:
        await delete_otp(email)
        return cast(int, data["attempts"])

    # Preserve the remaining TTL so the expiry window isn't reset
    ttl = await client.ttl(key)
    if ttl > 0:
        await client.setex(key, ttl, json.dumps(data))

    return cast(int, data["attempts"])


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------


async def check_otp_rate_limit(email: str) -> bool:
    """
    Check whether the user is still within the OTP request rate limit.

    Limit: OTP_RATE_LIMIT_REQUESTS per OTP_RATE_LIMIT_WINDOW_MINUTES.

    Returns:
        True  – request is allowed.
        False – limit exceeded.
    """
    client = await get_redis()
    key = f"otp_rate_limit:{email}"

    count = await client.incr(key)

    # Attach an expiry only on the very first increment inside the window
    if count == 1:
        await client.expire(key, timedelta(minutes=settings.OTP_RATE_LIMIT_WINDOW_MINUTES))

    return count <= settings.OTP_RATE_LIMIT_REQUESTS

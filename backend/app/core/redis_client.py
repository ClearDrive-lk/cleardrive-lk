# backend/app/core/redis_client.py

from __future__ import annotations

from typing import Optional

import redis.asyncio as redis  # type: ignore[import-untyped]
from .config import settings

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance (singleton).

    Returns:
        Redis client
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )

    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None

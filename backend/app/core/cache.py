"""
Redis cache service for query responses.
Story: CD-21.6
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class CacheService:
    """Lightweight async Redis cache wrapper."""

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl

    def generate_key(self, prefix: str, **params: Any) -> str:
        """Create a deterministic cache key from parameters."""
        sorted_params = sorted(params.items(), key=lambda item: item[0])
        payload = json.dumps(sorted_params, default=str, sort_keys=True)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    async def get(self, key: str) -> Optional[Any]:
        """Get JSON payload from cache."""
        try:
            redis = await get_redis()
            value = await redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache get failed for key '%s': %s", key, exc)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set JSON payload in cache with TTL."""
        try:
            redis = await get_redis()
            await redis.setex(key, ttl or self.default_ttl, json.dumps(value, default=str))
            return True
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache set failed for key '%s': %s", key, exc)
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            redis = await get_redis()
            keys = await redis.keys(pattern)
            if not keys:
                return 0
            return int(await redis.delete(*keys))
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache clear failed for pattern '%s': %s", pattern, exc)
            return 0


cache = CacheService()

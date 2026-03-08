"""Redis-backed webhook idempotency (CD-42.3)."""

from __future__ import annotations

from app.core.redis_client import get_redis


class PaymentIdempotencyService:
    """Track processed PayHere webhooks in Redis."""

    @staticmethod
    def _webhook_key(payment_id: str) -> str:
        return f"webhook_processed:{payment_id}"

    async def is_webhook_processed(self, payment_id: str) -> bool:
        redis = await get_redis()
        return bool(await redis.exists(self._webhook_key(payment_id)))

    async def mark_webhook_processed(self, payment_id: str, ttl_seconds: int = 3600) -> None:
        redis = await get_redis()
        await redis.setex(self._webhook_key(payment_id), ttl_seconds, "processed")


payment_idempotency = PaymentIdempotencyService()

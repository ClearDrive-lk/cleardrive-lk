# backend/app/core/rate_limit.py

"""
Tiered rate limiting based on user reputation.

Tiers:
- SUSPICIOUS: 30 req/min (flagged behavior)
- STANDARD: 100 req/min (normal users)
- TRUSTED: 200 req/min (KYC verified + 5+ orders)
"""

from datetime import datetime
from functools import wraps
from typing import Optional

from app.core.redis_client import get_redis
from app.modules.auth.models import User
from fastapi import HTTPException, Request, status


class UserTier:
    """User reputation tiers."""

    SUSPICIOUS = "suspicious"
    STANDARD = "standard"
    TRUSTED = "trusted"


# Rate limits per tier (requests per minute)
TIER_LIMITS = {
    UserTier.SUSPICIOUS: {
        "api_general": 30,
        "orders": 3,
        "payments": 2,
        "kyc": 2,
    },
    UserTier.STANDARD: {
        "api_general": 100,
        "orders": 10,
        "payments": 5,
        "kyc": 3,
    },
    UserTier.TRUSTED: {
        "api_general": 200,
        "orders": 20,
        "payments": 10,
        "kyc": 5,
    },
}


def get_user_tier(user: Optional[User]) -> str:
    """
    Determine user tier based on behavior and status.

    Args:
        user: User object or None (anonymous)

    Returns:
        User tier string
    """
    if user is None:
        return UserTier.STANDARD

    # Check for suspicious activity
    if user.failed_auth_attempts > 5:
        return UserTier.SUSPICIOUS

    # TODO: Check security_alerts from user_reputation table
    # if user.reputation and user.reputation.security_alerts > 3:
    #     return UserTier.SUSPICIOUS

    # Check for trusted status (KYC + completed orders)
    # TODO: Implement when KYC and Order models are connected
    # if user.kyc_verified and user.completed_orders > 5:
    #     return UserTier.TRUSTED

    return UserTier.STANDARD


def get_rate_limit(tier: str, endpoint_type: str = "api_general") -> int:
    """
    Get rate limit for tier and endpoint type.

    Args:
        tier: User tier
        endpoint_type: Type of endpoint (api_general, orders, payments, kyc)

    Returns:
        Rate limit (requests per minute)
    """
    limits = TIER_LIMITS.get(tier, TIER_LIMITS[UserTier.STANDARD])
    return limits.get(endpoint_type, limits["api_general"])


async def check_rate_limit(
    request: Request, user: Optional[User] = None, endpoint_type: str = "api_general"
) -> bool:
    """
    Check if request should be rate limited.

    Args:
        request: FastAPI request object
        user: Current user (if authenticated)
        endpoint_type: Type of endpoint

    Returns:
        True if within limits, raises HTTPException if exceeded
    """
    redis = await get_redis()

    # Determine identifier (user ID or IP)
    if user:
        identifier = f"user:{user.id}"
    else:
        # For anonymous users, use IP
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"

    # Get user tier
    tier = get_user_tier(user)
    limit = get_rate_limit(tier, endpoint_type)

    # Redis key
    window = 60  # 1 minute window
    current_minute = datetime.utcnow().strftime("%Y%m%d%H%M")
    key = f"rate_limit:{identifier}:{endpoint_type}:{current_minute}"

    try:
        # Increment counter
        current = await redis.incr(key)

        # Set expiry on first request
        if current == 1:
            await redis.expire(key, window)

        # Check if limit exceeded
        if current > limit:
            # Log rate limit violation
            # TODO: Store in rate_limit_violations table

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": tier,
                    "limit": limit,
                    "window": "1 minute",
                    "retry_after": window,
                },
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        # If Redis is down, allow request (fail open)
        print(f"Rate limit check failed: {e}")
        return True


# ============================================================================
# RATE LIMIT DECORATORS
# ============================================================================


def rate_limit(endpoint_type: str = "api_general"):
    """
    Rate limit decorator for endpoints.

    Usage:
        @router.post("/orders")
        @rate_limit("orders")
        async def create_order(...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from kwargs
            request = kwargs.get("request")
            user = kwargs.get("current_user")

            if request:
                await check_rate_limit(request, user, endpoint_type)

            return await func(*args, **kwargs)

        return wrapper

    return decorator

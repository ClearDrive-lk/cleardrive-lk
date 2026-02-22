# backend/app/core/redis.py

"""
Redis client and utilities for OTP, token, and session management.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, cast

import redis.asyncio as redis  # type: ignore[import-untyped]

from .config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# CLIENT SINGLETON
# ============================================================================

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
        await _redis_client.aclose()
        _redis_client = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    await get_redis()


# ============================================================================
# OTP STORAGE
# ============================================================================


async def store_otp(email: str, otp: str, expiry_minutes: int = 5) -> bool:
    """
    Store OTP in Redis with expiry.

    Redis Key: otp:{email}
    Value (JSON):
        {
            "otp": "123456",
            "created_at": "2026-01-23T10:30:00",
            "attempts": 0
        }

    Args:
        email: User email
        otp: One-time password
        expiry_minutes: OTP validity period (default: 5)

    Returns:
        True if stored successfully
    """
    client = await get_redis()
    key = f"otp:{email}"

    value = json.dumps(
        {
            "otp": otp,
            "created_at": datetime.now(UTC).isoformat(),
            "attempts": 0,
        }
    )

    await client.setex(key, timedelta(minutes=expiry_minutes), value)
    return True


async def get_otp(email: str) -> Optional[dict]:
    """
    Retrieve OTP data from Redis.

    Args:
        email: User email

    Returns:
        OTP data or None if expired/not found
    """
    client = await get_redis()
    value = await client.get(f"otp:{email}")

    if not value:
        return None

    return cast(Optional[dict], json.loads(value))


async def delete_otp(email: str) -> bool:
    """
    Delete OTP from Redis (one-time use).

    Args:
        email: User email

    Returns:
        True if deleted
    """
    client = await get_redis()
    await client.delete(f"otp:{email}")
    return True


async def increment_otp_attempts(email: str) -> int:
    """
    Increment failed OTP verification attempts.
    Deletes the OTP once OTP_MAX_ATTEMPTS is reached.

    Args:
        email: User email

    Returns:
        Current attempt count (0 if the key no longer exists)
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


# ============================================================================
# RATE LIMITING
# ============================================================================


async def check_otp_rate_limit(email: str) -> bool:
    """
    Check whether the user is still within the OTP request rate limit.

    Limit: OTP_RATE_LIMIT_REQUESTS per OTP_RATE_LIMIT_WINDOW_MINUTES.

    Args:
        email: User email

    Returns:
        True if request is allowed, False if limit exceeded
    """
    client = await get_redis()
    key = f"otp_rate_limit:{email}"

    count = await client.incr(key)

    # Attach an expiry only on the very first increment inside the window
    if count == 1:
        await client.expire(key, timedelta(minutes=settings.OTP_RATE_LIMIT_WINDOW_MINUTES))

    return count <= settings.OTP_RATE_LIMIT_REQUESTS


# ============================================================================
# TOKEN BLACKLIST
# ============================================================================


async def blacklist_token(token_jti: str, ttl_seconds: int) -> bool:
    """
    Add token to blacklist.

    Args:
        token_jti: JWT ID (jti claim)
        ttl_seconds: How long to blacklist (remaining token lifetime)

    Returns:
        True if blacklisted successfully

    Redis Key: blacklist:{token_jti}
    Value: {blacklisted_at, reason}
    """
    client = await get_redis()
    key = f"blacklist:{token_jti}"

    value = json.dumps({"blacklisted_at": datetime.now(UTC).isoformat(), "reason": "logout"})

    await client.setex(key, ttl_seconds, value)
    return True


async def is_token_blacklisted(token_jti: str) -> bool:
    """
    Check if token is blacklisted.

    Args:
        token_jti: JWT ID

    Returns:
        True if blacklisted
    """
    client = await get_redis()
    key = f"blacklist:{token_jti}"
    return await client.exists(key) > 0


async def detect_token_reuse(token_jti: str) -> bool:
    """
    Detect if refresh token has been reused.

    Token reuse indicates possible theft:
    - User A has token
    - Token stolen by attacker B
    - A refreshes token (blacklists old one)
    - B tries to use old token → REUSE DETECTED

    Args:
        token_jti: JWT ID

    Returns:
        True if reuse detected
    """
    # If token is blacklisted but signature is still valid,
    # it means someone is trying to reuse a rotated token
    return await is_token_blacklisted(token_jti)


# ============================================================================
# REFRESH TOKEN STORAGE
# ============================================================================


async def store_refresh_token(
    token_jti: str, user_id: str, device_info: Dict, ttl_days: int = 30
) -> bool:
    """
    Store refresh token metadata.

    Args:
        token_jti: JWT ID
        user_id: User ID
        device_info: Device metadata (IP, user agent)
        ttl_days: TTL in days (default: 30)

    Returns:
        True if stored

    Redis Key: refresh_token:{token_jti}
    Value: {user_id, device_info, created_at}
    """
    client = await get_redis()
    key = f"refresh_token:{token_jti}"

    value = json.dumps(
        {
            "user_id": user_id,
            "device_info": device_info,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )

    await client.setex(key, timedelta(days=ttl_days), value)

    return True


async def get_refresh_token(token_jti: str) -> Optional[Dict]:
    """
    Get refresh token metadata.

    Args:
        token_jti: JWT ID

    Returns:
        Token metadata or None
    """
    client = await get_redis()
    key = f"refresh_token:{token_jti}"
    value = await client.get(key)

    if not value:
        return None

    return cast(Dict[str, Any], json.loads(value))


async def delete_refresh_token(token_jti: str) -> bool:
    """
    Delete refresh token (on rotation).

    Args:
        token_jti: JWT ID

    Returns:
        True if deleted
    """
    client = await get_redis()
    key = f"refresh_token:{token_jti}"
    await client.delete(key)
    return True


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


async def create_session(
    user_id: str,
    session_id: str,
    token_jti: str,
    ip_address: str,
    user_agent: str,
    ttl_days: int = 30,
) -> bool:
    """
    Create user session.

    Args:
        user_id: User ID
        session_id: Session ID
        token_jti: JWT ID of refresh token
        ip_address: Client IP
        user_agent: Client user agent
        ttl_days: TTL in days

    Returns:
        True if created

    Redis Key: session:{user_id}:{session_id}
    Value: {token_jti, ip, user_agent, created_at, last_active}
    """
    client = await get_redis()
    key = f"session:{user_id}:{session_id}"

    value = json.dumps(
        {
            "token_jti": token_jti,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.now(UTC).isoformat(),
            "last_active": datetime.now(UTC).isoformat(),
        }
    )

    await client.setex(key, timedelta(days=ttl_days), value)

    return True


async def get_user_sessions(user_id: str) -> List[Dict]:
    """
    Get all sessions for a user.

    Args:
        user_id: User ID

    Returns:
        List of session data
    """
    client = await get_redis()
    pattern = f"session:{user_id}:*"
    keys = await client.keys(pattern)

    sessions = []
    for key in keys:
        value = await client.get(key)
        if value:
            session_data = json.loads(value)
            session_data["session_id"] = key.split(":")[-1]
            sessions.append(session_data)

    return sessions


async def get_session_count(user_id: str) -> int:
    """
    Get number of active sessions for a user.

    Args:
        user_id: User UUID as string

    Returns:
        Number of active sessions

    Example:
        count = await get_session_count("123e4567-e89b-12d3-a456-426614174000")
        # Returns: 3
    """
    client = await get_redis()
    pattern = f"session:{user_id}:*"
    keys = await client.keys(pattern)
    return len(keys)


async def delete_session(user_id: str, session_id: str) -> bool:
    """
    Delete specific session.

    Args:
        user_id: User ID
        session_id: Session ID

    Returns:
        True if deleted
    """
    client = await get_redis()
    key = f"session:{user_id}:{session_id}"
    await client.delete(key)
    return True


async def delete_all_user_sessions(user_id: str) -> int:
    """
    Delete all sessions for a user.

    Used when token reuse detected (security measure).

    Args:
        user_id: User ID

    Returns:
        Number of sessions deleted
    """
    client = await get_redis()
    pattern = f"session:{user_id}:*"
    keys = await client.keys(pattern)

    if keys:
        await client.delete(*keys)

    return len(keys)


async def enforce_session_limit(user_id: str, max_sessions: Optional[int] = None) -> Dict[str, Any]:
    """
    Enforce maximum concurrent sessions per user.

    If user has more than max_sessions, delete oldest sessions
    until count equals max_sessions.

    Args:
        user_id: User UUID as string
        max_sessions: Maximum allowed sessions (default from settings.MAX_SESSIONS_PER_USER)

    Returns:
        {
            "sessions_deleted": 2,
            "current_count": 5,
            "limit": 5
        }

    Example:
        # User has 7 sessions, max is 5
        result = await enforce_session_limit(user_id)
        # Result: {"sessions_deleted": 2, "current_count": 5, "limit": 5}
    """
    # Use default from settings if not provided
    if max_sessions is None:
        max_sessions = getattr(settings, "MAX_SESSIONS_PER_USER", 5)

    # Get all user sessions
    sessions = await get_user_sessions(user_id)

    result = {
        "sessions_deleted": 0,
        "current_count": len(sessions),
        "limit": max_sessions,
    }

    # If within limit, no action needed
    if len(sessions) <= max_sessions:
        return result

    # Sort by created_at (oldest first)
    sessions.sort(key=lambda s: s.get("created_at", ""))

    # Calculate how many to delete
    num_to_delete = len(sessions) - max_sessions

    logger.info(
        f"Enforcing session limit for user {user_id}: " f"deleting {num_to_delete} oldest sessions"
    )

    # Delete oldest sessions
    for session in sessions[:num_to_delete]:
        session_id = session.get("session_id")
        token_jti = session.get("token_jti")

        if session_id:
            # Delete session
            await delete_session(user_id, session_id)

            # Blacklist associated refresh token
            if token_jti:
                # Blacklist for remaining TTL (max 30 days)
                await blacklist_token(token_jti, 30 * 24 * 60 * 60)

            result["sessions_deleted"] += 1

    result["current_count"] = len(sessions) - result["sessions_deleted"]

    logger.info(
        f"Session limit enforced for user {user_id}",
        extra={
            "user_id": user_id,
            "sessions_deleted": result["sessions_deleted"],
            "current_count": result["current_count"],
        },
    )

    return result

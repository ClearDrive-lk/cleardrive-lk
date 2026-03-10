"""
Tiered rate limiting based on account trust and security signals.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis import get_redis
from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import User
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.security.models import (
    RateLimitViolation,
    SecurityEvent,
    SecurityEventType,
    Severity,
    UserReputation,
)
from app.modules.security.models import UserTier as ReputationTier
from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserTier(str, Enum):
    """Normalized rate-limit tiers."""

    SUSPICIOUS = "suspicious"
    STANDARD = "standard"
    TRUSTED = "trusted"


TIER_LIMITS: dict[UserTier, dict[str, dict[str, int]]] = {
    UserTier.SUSPICIOUS: {
        "api_general": {"minute": 5, "hour": 50},
        "orders": {"minute": 5, "hour": 50},
        "payments": {"minute": 5, "hour": 50},
        "kyc": {"minute": 5, "hour": 50},
        "chat": {"minute": 5, "hour": 50},
    },
    UserTier.STANDARD: {
        "api_general": {"minute": 30, "hour": 500},
        "orders": {"minute": 15, "hour": 200},
        "payments": {"minute": 10, "hour": 100},
        "kyc": {"minute": 10, "hour": 100},
        "chat": {"minute": 10, "hour": 200},
    },
    UserTier.TRUSTED: {
        "api_general": {"minute": 100, "hour": 2000},
        "orders": {"minute": 40, "hour": 600},
        "payments": {"minute": 20, "hour": 200},
        "kyc": {"minute": 15, "hour": 150},
        "chat": {"minute": 20, "hour": 400},
    },
}

SUSPICIOUS_USER_AGENT_PATTERNS = (
    r"bot\b",
    r"crawler",
    r"spider",
    r"headless",
    r"scrapy",
    r"python-requests",
    r"curl/",
    r"wget/",
)

_fallback_rate_limits: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "unknown")


def _reputation_to_tier(tier: ReputationTier | None) -> UserTier:
    if tier == ReputationTier.SUSPICIOUS:
        return UserTier.SUSPICIOUS
    if tier == ReputationTier.TRUSTED:
        return UserTier.TRUSTED
    return UserTier.STANDARD


def _tier_to_reputation(tier: UserTier) -> ReputationTier:
    if tier == UserTier.SUSPICIOUS:
        return ReputationTier.SUSPICIOUS
    if tier == UserTier.TRUSTED:
        return ReputationTier.TRUSTED
    return ReputationTier.STANDARD


def get_endpoint_type(path: str) -> str:
    """Map request paths to rate-limit buckets."""
    if "/chat/" in path:
        return "chat"
    if "/orders" in path:
        return "orders"
    if "/payments" in path:
        return "payments"
    if "/kyc" in path:
        return "kyc"
    return "api_general"


def get_rate_limit(tier: UserTier | str, endpoint_type: str = "api_general") -> dict[str, int]:
    """Get minute/hour limits for a tier and endpoint type."""
    if isinstance(tier, UserTier):
        normalized = tier
    else:
        normalized = UserTier(str(tier).split(".")[-1].lower())
    limits = TIER_LIMITS.get(normalized, TIER_LIMITS[UserTier.STANDARD])
    return limits.get(endpoint_type, limits["api_general"])


def _ensure_reputation(user: User, db: Session) -> UserReputation:
    reputation = db.query(UserReputation).filter(UserReputation.user_id == user.id).first()
    if reputation is None:
        reputation = UserReputation(user_id=user.id, current_tier=ReputationTier.STANDARD)
        db.add(reputation)
        db.flush()
    return reputation


def determine_user_tier(user: User | None, db: Session | None = None) -> UserTier:
    """
    Determine user tier based on behavior, age, and verification state.
    """
    if user is None:
        return UserTier.STANDARD

    owns_db = db is None
    session = db or SessionLocal()
    try:
        reputation = session.query(UserReputation).filter(UserReputation.user_id == user.id).first()

        recent_auth_failure = (
            user.failed_auth_attempts >= settings.SUSPICIOUS_ACTIVITY_THRESHOLD
            and user.last_failed_auth is not None
            and user.last_failed_auth >= datetime.now(UTC) - timedelta(minutes=10)
        )
        if recent_auth_failure:
            return UserTier.SUSPICIOUS

        if reputation is not None:
            if reputation.current_tier == ReputationTier.SUSPICIOUS:
                return UserTier.SUSPICIOUS
            if reputation.security_alerts >= settings.SUSPICIOUS_ACTIVITY_THRESHOLD:
                return UserTier.SUSPICIOUS
            if reputation.impossible_travel_detected or reputation.multiple_devices_flagged:
                return UserTier.SUSPICIOUS

        account_age = datetime.now(UTC) - user.created_at.replace(tzinfo=UTC)
        approved_kyc = (
            session.query(KYCDocument)
            .filter(KYCDocument.user_id == user.id, KYCDocument.status == KYCStatus.APPROVED)
            .first()
            is not None
        )

        if approved_kyc and account_age >= timedelta(days=30):
            return UserTier.TRUSTED

        return UserTier.STANDARD
    finally:
        if owns_db:
            session.close()


async def get_user_tier(user: User | None, db: Session | None = None) -> UserTier:
    """
    Get the user tier from Redis or calculate and persist it.
    """
    if user is None:
        return UserTier.STANDARD

    redis = await get_redis()
    cache_key = f"user_tier:{user.id}"
    cached = await redis.get(cache_key)
    if cached:
        try:
            return UserTier(str(cached).lower())
        except ValueError:
            logger.warning("Ignoring invalid cached tier %s for user %s", cached, user.id)

    owns_db = db is None
    session = db or SessionLocal()
    try:
        tier = determine_user_tier(user, session)
        reputation = _ensure_reputation(user, session)
        new_reputation_tier = _tier_to_reputation(tier)
        if reputation.current_tier != new_reputation_tier:
            reputation.current_tier = new_reputation_tier
            session.commit()
        await redis.set(cache_key, tier.value)
        return tier
    finally:
        if owns_db:
            session.close()


async def _write_tier_to_redis(user_id: Any, tier: UserTier) -> None:
    redis = await get_redis()
    await redis.set(f"user_tier:{user_id}", tier.value)


async def set_user_tier(
    user: User,
    tier: UserTier,
    db: Session,
    *,
    reason: str,
    request: Request | None = None,
    alert_ttl_seconds: int | None = None,
    manual_review: bool = False,
) -> bool:
    """
    Persist a user tier update with security and audit logging.
    """
    reputation = _ensure_reputation(user, db)
    previous_tier = _reputation_to_tier(reputation.current_tier)
    reputation.current_tier = _tier_to_reputation(tier)
    if tier == UserTier.SUSPICIOUS:
        reputation.security_alerts += 1

    db.add(
        SecurityEvent(
            event_type=(
                SecurityEventType.SUSPICIOUS_ACTIVITY
                if tier == UserTier.SUSPICIOUS
                else SecurityEventType.UNAUTHORIZED_ACCESS
            ),
            severity=Severity.HIGH if tier == UserTier.SUSPICIOUS else Severity.MEDIUM,
            user_id=user.id,
            ip_address=_client_ip(request) if request is not None else None,
            user_agent=_user_agent(request) if request is not None else None,
            details={
                "reason": reason,
                "from_tier": previous_tier.value,
                "to_tier": tier.value,
                "manual_review": manual_review,
            },
        )
    )

    if previous_tier != tier:
        db.add(
            AuditLog(
                event_type=(
                    AuditEventType.USER_TIER_DOWNGRADED
                    if tier == UserTier.SUSPICIOUS
                    else AuditEventType.USER_TIER_UPGRADED
                ),
                user_id=user.id,
                details={
                    "reason": reason,
                    "from_tier": previous_tier.value,
                    "to_tier": tier.value,
                    "manual_review": manual_review,
                },
            )
        )

    db.commit()
    await _write_tier_to_redis(user.id, tier)

    redis = await get_redis()
    suspicious_key = f"suspicious_activity:{user.id}"
    if tier == UserTier.SUSPICIOUS:
        payload = json.dumps(
            {
                "reason": reason,
                "manual_review": manual_review,
                "flagged_at": datetime.now(UTC).isoformat(),
            }
        )
        if alert_ttl_seconds:
            await redis.setex(suspicious_key, alert_ttl_seconds, payload)
        else:
            await redis.set(suspicious_key, payload)
    else:
        await redis.delete(suspicious_key)

    return previous_tier != tier


async def flag_user_suspicious(
    user: User,
    db: Session,
    *,
    reason: str,
    request: Request | None = None,
    alert_ttl_seconds: int = 24 * 60 * 60,
    manual_review: bool = False,
) -> bool:
    """Downgrade the user to the suspicious tier."""
    return await set_user_tier(
        user,
        UserTier.SUSPICIOUS,
        db,
        reason=reason,
        request=request,
        alert_ttl_seconds=alert_ttl_seconds,
        manual_review=manual_review,
    )


async def record_failed_login(user: User, db: Session, request: Request | None = None) -> None:
    """
    Record a failed login and auto-downgrade if the threshold is reached.
    """
    user.failed_auth_attempts = (user.failed_auth_attempts or 0) + 1
    user.last_failed_auth = datetime.now(UTC)
    db.commit()

    if user.failed_auth_attempts >= settings.SUSPICIOUS_ACTIVITY_THRESHOLD:
        await flag_user_suspicious(
            user,
            db,
            reason="3+ failed login attempts in 10 minutes",
            request=request,
            alert_ttl_seconds=24 * 60 * 60,
            manual_review=True,
        )


async def clear_failed_login_state(user: User, db: Session) -> None:
    """Reset the failed login counters after a successful authentication."""
    user.failed_auth_attempts = 0
    user.last_failed_auth = None
    db.commit()


async def _record_request_patterns(
    request: Request,
    user: User | None,
    db: Session | None,
    tier: UserTier,
    current_minute_count: int,
    minute_limit: int,
) -> None:
    if user is None or db is None:
        return

    redis = await get_redis()
    now = datetime.now(UTC).timestamp()

    rapid_key = f"rapid_requests:{user.id}"
    rapid_raw = await redis.get(rapid_key)
    rapid_events = json.loads(rapid_raw) if rapid_raw else []
    rapid_events = [ts for ts in rapid_events if now - float(ts) <= 10]
    rapid_events.append(now)
    await redis.setex(rapid_key, 3600, json.dumps(rapid_events[-20:]))

    last_ten = rapid_events[-10:]
    if len(last_ten) == 10 and all(
        float(b) - float(a) < 1.0 for a, b in zip(last_ten, last_ten[1:])
    ):
        await flag_user_suspicious(
            user,
            db,
            reason="10+ rapid requests detected",
            request=request,
            alert_ttl_seconds=3600,
        )

    ip_key = f"user_ips:{user.id}"
    ip_raw = await redis.get(ip_key)
    ip_map = json.loads(ip_raw) if ip_raw else {}
    ip_map = {ip: ts for ip, ts in ip_map.items() if now - float(ts) <= 3600}
    ip_map[_client_ip(request)] = now
    await redis.setex(ip_key, 3600, json.dumps(ip_map))

    if len(ip_map) >= 5:
        await flag_user_suspicious(
            user,
            db,
            reason="Multiple IP addresses detected in 1 hour",
            request=request,
            alert_ttl_seconds=24 * 60 * 60,
            manual_review=True,
        )

    if re.search("|".join(SUSPICIOUS_USER_AGENT_PATTERNS), _user_agent(request), re.IGNORECASE):
        await flag_user_suspicious(
            user,
            db,
            reason="Suspicious user agent detected",
            request=request,
            alert_ttl_seconds=3600,
        )

    if current_minute_count >= minute_limit * 2 and tier != UserTier.SUSPICIOUS:
        await flag_user_suspicious(
            user,
            db,
            reason="Repeated rate limit violations detected",
            request=request,
            alert_ttl_seconds=24 * 60 * 60,
        )


async def _log_rate_limit_violation(
    request: Request,
    user: User | None,
    db: Session | None,
    tier: UserTier,
    endpoint_type: str,
    attempted: int,
    limit: int,
) -> None:
    if db is None:
        return

    db.add(
        RateLimitViolation(
            user_id=user.id if user is not None else None,
            ip_address=_client_ip(request),
            endpoint=request.url.path,
            limit_tier=tier.value,
            requests_attempted=attempted,
            limit_exceeded=attempted - limit,
        )
    )
    db.add(
        SecurityEvent(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            severity=Severity.MEDIUM,
            user_id=user.id if user is not None else None,
            ip_address=_client_ip(request),
            user_agent=_user_agent(request),
            details={
                "endpoint_type": endpoint_type,
                "path": request.url.path,
                "tier": tier.value,
                "attempted": attempted,
                "limit": limit,
            },
        )
    )
    db.commit()


def apply_rate_limit_headers(response: Response, request: Request) -> None:
    """Attach rate-limit headers when the request was checked successfully."""
    context = getattr(request.state, "rate_limit_context", None)
    if not context:
        return

    response.headers["X-RateLimit-Tier"] = context["tier"]
    response.headers["X-RateLimit-Limit-Minute"] = str(context["minute_limit"])
    response.headers["X-RateLimit-Remaining-Minute"] = str(context["minute_remaining"])
    response.headers["X-RateLimit-Limit-Hour"] = str(context["hour_limit"])
    response.headers["X-RateLimit-Remaining-Hour"] = str(context["hour_remaining"])


async def check_rate_limit(
    request: Request,
    user: User | None = None,
    endpoint_type: str = "api_general",
    db: Session | None = None,
) -> bool:
    """
    Check whether a request is within the configured tier limits.
    """
    tier = UserTier.STANDARD
    limits = get_rate_limit(tier, endpoint_type)

    identifier = f"user:{user.id}" if user is not None else f"ip:{_client_ip(request)}"
    now = datetime.now(UTC)
    minute_key = f"rate_limit:{identifier}:{endpoint_type}:minute:{now.strftime('%Y%m%d%H%M')}"
    hour_key = f"rate_limit:{identifier}:{endpoint_type}:hour:{now.strftime('%Y%m%d%H')}"

    try:
        tier = await get_user_tier(user, db)
        limits = get_rate_limit(tier, endpoint_type)
        redis = await get_redis()
        current_minute = int(await redis.incr(minute_key))
        if current_minute == 1:
            await redis.expire(minute_key, 60)

        current_hour = int(await redis.incr(hour_key))
        if current_hour == 1:
            await redis.expire(hour_key, 3600)

        await _record_request_patterns(request, user, db, tier, current_minute, limits["minute"])

        request.state.rate_limit_context = {
            "tier": tier.value,
            "minute_limit": limits["minute"],
            "minute_remaining": max(limits["minute"] - current_minute, 0),
            "hour_limit": limits["hour"],
            "hour_remaining": max(limits["hour"] - current_hour, 0),
        }

        retry_after = 60
        breached_limit = limits["minute"]
        breached_window = "1 minute"
        attempted = current_minute

        if current_hour > limits["hour"]:
            retry_after = 3600
            breached_limit = limits["hour"]
            breached_window = "1 hour"
            attempted = current_hour

        if current_minute > limits["minute"] or current_hour > limits["hour"]:
            await _log_rate_limit_violation(
                request, user, db, tier, endpoint_type, attempted, breached_limit
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": tier.value,
                    "limit": breached_limit,
                    "window": breached_window,
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after), "X-RateLimit-Tier": tier.value},
            )

        return True

    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Rate limit check failed, using fallback: %s", exc)
        fallback_key = f"{identifier}:{endpoint_type}:{now.strftime('%Y%m%d%H%M')}"
        now_ts = now.timestamp()
        recent_calls = [
            ts for ts in _fallback_rate_limits.get(fallback_key, []) if now_ts - ts < 60
        ]

        if len(recent_calls) >= limits["minute"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": tier.value,
                    "limit": limits["minute"],
                    "window": "1 minute",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60", "X-RateLimit-Tier": tier.value},
            )

        recent_calls.append(now_ts)
        _fallback_rate_limits[fallback_key] = recent_calls
        request.state.rate_limit_context = {
            "tier": tier.value,
            "minute_limit": limits["minute"],
            "minute_remaining": max(limits["minute"] - len(recent_calls), 0),
            "hour_limit": limits["hour"],
            "hour_remaining": limits["hour"],
        }
        return True


def rate_limit(endpoint_type: str = "api_general"):
    """Decorator form kept for compatibility with existing routes."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            user = kwargs.get("current_user")
            db = kwargs.get("db")

            if request is not None:
                await check_rate_limit(request, user, endpoint_type, db=db)

            response = await func(*args, **kwargs)
            if isinstance(response, Response) and request is not None:
                apply_rate_limit_headers(response, request)
            return response

        return wrapper

    return decorator

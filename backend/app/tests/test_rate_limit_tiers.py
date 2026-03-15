from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.rate_limit import UserTier, determine_user_tier, record_failed_login
from app.modules.kyc.models import KYCDocument, KYCStatus
from app.modules.security.models import SecurityEvent, SecurityEventType, UserReputation
from app.modules.security.models import UserTier as ReputationTier


def test_determine_user_tier_returns_trusted_for_old_kyc_verified_user(db, test_user):
    test_user.created_at = datetime.now(UTC) - timedelta(days=31)
    db.add(
        KYCDocument(
            user_id=test_user.id,
            nic_front_url="front",
            nic_back_url="back",
            selfie_url="selfie",
            status=KYCStatus.APPROVED,
        )
    )
    db.commit()

    tier = determine_user_tier(test_user, db)

    assert tier == UserTier.TRUSTED


@pytest.mark.asyncio
async def test_failed_login_threshold_downgrades_user_to_suspicious(db, test_user, mock_redis):
    for _ in range(3):
        await record_failed_login(test_user, db)

    db.refresh(test_user)
    reputation = db.query(UserReputation).filter(UserReputation.user_id == test_user.id).first()

    assert test_user.failed_auth_attempts == 3
    assert reputation is not None
    assert reputation.current_tier == ReputationTier.SUSPICIOUS
    assert await mock_redis.get(f"user_tier:{test_user.id}") == UserTier.SUSPICIOUS.value


def test_rate_limit_middleware_applies_to_authenticated_endpoints(client, auth_headers, db):
    limited = None
    successful_requests = 0

    for _ in range(35):
        response = client.get("/api/v1/auth/sessions", headers=auth_headers)
        if response.status_code == 429:
            limited = response
            break
        successful_requests += 1
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Tier"] == UserTier.STANDARD.value

    assert successful_requests >= 10
    assert limited is not None
    assert limited.status_code == 429
    assert limited.json()["detail"]["tier"] in {
        UserTier.STANDARD.value,
        UserTier.SUSPICIOUS.value,
    }

    event = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.event_type == SecurityEventType.RATE_LIMIT_EXCEEDED)
        .first()
    )
    assert event is not None

from __future__ import annotations

import pytest
from app.core.rate_limit import record_failed_login
from app.modules.security.models import SecurityEvent, SecurityEventType


@pytest.mark.asyncio
async def test_failed_login_creates_security_event(db, test_user):
    await record_failed_login(test_user, db)

    event = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.user_id == test_user.id,
            SecurityEvent.event_type == SecurityEventType.AUTH_FAILURE,
        )
        .first()
    )

    assert event is not None
    assert event.details["attempt"] == 1
    assert event.details["reason"] == "invalid_password"

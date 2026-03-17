from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.security.models import SecurityEvent, SecurityEventType, Severity


def test_admin_security_events_endpoint_returns_stats_and_events(client, db, admin_headers):
    now = datetime.now(UTC)
    events = [
        SecurityEvent(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity=Severity.MEDIUM,
            user_id=None,
            ip_address="10.0.0.1",
            user_agent="test-agent",
            country_code="US",
            details={"reason": "invalid_password"},
            created_at=now - timedelta(hours=1),
        ),
        SecurityEvent(
            event_type=SecurityEventType.IMPOSSIBLE_TRAVEL,
            severity=Severity.HIGH,
            user_id=None,
            ip_address="10.0.0.2",
            user_agent="test-agent",
            country_code="LK",
            details={"reason": "impossible_travel"},
            created_at=now - timedelta(hours=2),
        ),
    ]
    db.add_all(events)
    db.commit()

    response = client.get("/api/v1/admin/security/events", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["stats"]["total_events"] >= 2
    assert payload["stats"]["severity_breakdown"]["MEDIUM"] >= 1
    assert payload["stats"]["top_event_types"]["AUTH_FAILURE"] >= 1
    assert payload["recent_events"]["total"] >= 2
    assert len(payload["recent_events"]["events"]) >= 1

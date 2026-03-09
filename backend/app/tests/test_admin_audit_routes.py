from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import Role, User


def _create_audit_log(
    db,
    *,
    event_type: AuditEventType,
    user_id=None,
    admin_id=None,
    details: dict | None = None,
    created_at: datetime | None = None,
):
    log = AuditLog(
        event_type=event_type,
        user_id=user_id,
        admin_id=admin_id,
        details=details or {},
        created_at=created_at or datetime.now(UTC),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def test_get_audit_logs_supports_filters_and_pagination(
    client, db, admin_headers, admin_user, test_user
):
    second_user = User(
        email="other@example.com",
        name="Other User",
        role=test_user.role,
        google_id="other-google-id",
    )
    db.add(second_user)
    db.commit()
    db.refresh(second_user)

    base_time = datetime(2026, 3, 9, 8, 0, tzinfo=UTC)
    _create_audit_log(
        db,
        event_type=AuditEventType.ROLE_CHANGED,
        user_id=test_user.id,
        admin_id=admin_user.id,
        details={"reason": "promoted to exporter"},
        created_at=base_time,
    )
    _create_audit_log(
        db,
        event_type=AuditEventType.GAZETTE_APPROVED,
        user_id=second_user.id,
        admin_id=admin_user.id,
        details={"gazette_no": "2026/02"},
        created_at=base_time + timedelta(hours=1),
    )
    _create_audit_log(
        db,
        event_type=AuditEventType.ROLE_CHANGED,
        user_id=test_user.id,
        admin_id=admin_user.id,
        details={"reason": "restored access"},
        created_at=base_time + timedelta(hours=2),
    )

    response = client.get(
        "/api/v1/admin/audit-logs",
        headers=admin_headers,
        params={
            "event_type": AuditEventType.ROLE_CHANGED.value,
            "user_id": str(test_user.id),
            "start_date": "2026-03-09T00:00:00+00:00",
            "end_date": "2026-03-09T23:59:59+00:00",
            "search": "access",
            "page": 1,
            "limit": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["limit"] == 1
    assert payload["total_pages"] == 1
    assert len(payload["logs"]) == 1
    assert payload["logs"][0]["event_type"] == AuditEventType.ROLE_CHANGED.value
    assert payload["logs"][0]["user_email"] == test_user.email
    assert payload["logs"][0]["admin_email"] == admin_user.email
    assert payload["logs"][0]["details"]["reason"] == "restored access"


def test_get_audit_event_types_lists_new_cd62_values(client, admin_headers):
    response = client.get("/api/v1/admin/audit-logs/event-types", headers=admin_headers)

    assert response.status_code == 200
    payload = response.json()
    assert AuditEventType.GAZETTE_APPROVED.value in payload["event_types"]
    assert AuditEventType.KYC_MANUAL_REVIEW_QUEUED.value in payload["event_types"]


def test_export_audit_logs_csv_returns_filtered_rows(client, db, admin_headers, admin_user):
    customer = User(
        email="csv-user@example.com",
        name="CSV User",
        role=Role.CUSTOMER,
        google_id="csv-user-google-id",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    _create_audit_log(
        db,
        event_type=AuditEventType.GAZETTE_REJECTED,
        user_id=customer.id,
        admin_id=admin_user.id,
        details={"reason": "Values do not match source document"},
    )

    response = client.get(
        "/api/v1/admin/audit-logs/export",
        headers=admin_headers,
        params={"event_type": AuditEventType.GAZETTE_REJECTED.value},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "audit-logs.csv" in response.headers["content-disposition"]
    assert "GAZETTE_REJECTED" in response.text
    assert "Values do not match source document" in response.text

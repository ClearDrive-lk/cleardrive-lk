from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID as PyUUID

from app.modules.auth.models import User
from app.modules.security.models import SecurityEvent, SecurityEventType, Severity
from fastapi import Request
from sqlalchemy.orm import Session


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.client.host if request.client else None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    return request.headers.get("user-agent")


def log_security_event(
    db: Session,
    *,
    event_type: SecurityEventType,
    severity: Severity,
    user: User | None = None,
    user_id: str | None = None,
    request: Request | None = None,
    country_code: str | None = None,
    details: dict[str, Any] | None = None,
) -> SecurityEvent:
    """
    Persist a security event with optional request/user context.
    """
    resolved_user_id: PyUUID | None
    if user is not None:
        resolved_user_id = user.id
    elif user_id is not None:
        resolved_user_id = PyUUID(str(user_id))
    else:
        resolved_user_id = None

    payload: dict[str, Any] = details.copy() if details else {}
    if user is not None:
        payload.setdefault("user_email", user.email)

    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        user_id=resolved_user_id,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
        country_code=country_code,
        details=payload or None,
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def mark_security_event_resolved(
    db: Session,
    event: SecurityEvent,
    *,
    resolved_by: str | None,
    resolution_note: str | None = None,
) -> SecurityEvent:
    """
    Resolve a security event and optionally append a resolution note.
    """
    event.resolved = True
    event.resolved_by = resolved_by
    event.resolved_at = datetime.now(UTC)

    if resolution_note:
        details = event.details or {}
        details["resolution_note"] = resolution_note
        details["resolved_at"] = event.resolved_at.isoformat()
        event.details = details

    db.commit()
    db.refresh(event)
    return event

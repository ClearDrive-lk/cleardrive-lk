from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from app.core.dependencies import get_current_active_user, get_db
from app.core.permissions import Permission, require_permission
from app.modules.auth.models import User
from app.modules.security.models import SecurityEvent
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/security", tags=["Admin Security"])


class SecurityEventItem(BaseModel):
    id: str
    event_type: str
    severity: str
    user_id: str | None
    ip_address: str | None
    country_code: str | None
    details: dict | None
    created_at: str
    resolved: bool


class SecurityEventList(BaseModel):
    events: List[SecurityEventItem]
    total: int


class SecurityEventStats(BaseModel):
    total_events: int
    severity_breakdown: Dict[str, int]
    top_event_types: Dict[str, int]
    top_ips: Dict[str, int]


class SecurityEventResponse(BaseModel):
    stats: SecurityEventStats
    recent_events: SecurityEventList


@router.get("/events", response_model=SecurityEventResponse)
async def get_security_events(
    days: int = Query(7, ge=1, le=90, description="Look-back window in days"),
    limit: int = Query(50, ge=1, le=200, description="Max recent events to return"),
    _: User = Depends(require_permission(Permission.MANAGE_SECURITY_EVENTS)),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Return recent security events and aggregate stats for the admin dashboard.
    """
    since = datetime.utcnow() - timedelta(days=days)

    base_query = db.query(SecurityEvent).filter(SecurityEvent.created_at >= since)

    total_events = base_query.count()

    severity_rows = (
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
        .filter(SecurityEvent.created_at >= since)
        .group_by(SecurityEvent.severity)
        .all()
    )
    severity_breakdown = {str(sev.value): count for sev, count in severity_rows}

    event_rows = (
        db.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .filter(SecurityEvent.created_at >= since)
        .group_by(SecurityEvent.event_type)
        .order_by(func.count(SecurityEvent.id).desc())
        .limit(5)
        .all()
    )
    top_event_types = {str(evt.value): count for evt, count in event_rows}

    ip_rows = (
        db.query(SecurityEvent.ip_address, func.count(SecurityEvent.id))
        .filter(and_(SecurityEvent.created_at >= since, SecurityEvent.ip_address.isnot(None)))
        .group_by(SecurityEvent.ip_address)
        .order_by(func.count(SecurityEvent.id).desc())
        .limit(5)
        .all()
    )
    top_ips = {str(ip): count for ip, count in ip_rows}

    recent_events = base_query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()

    events = [
        SecurityEventItem(
            id=str(event.id),
            event_type=event.event_type.value,
            severity=event.severity.value,
            user_id=str(event.user_id) if event.user_id else None,
            ip_address=event.ip_address,
            country_code=event.country_code,
            details=event.details,
            created_at=event.created_at.isoformat(),
            resolved=event.resolved,
        )
        for event in recent_events
    ]

    stats = SecurityEventStats(
        total_events=total_events,
        severity_breakdown=severity_breakdown,
        top_event_types=top_event_types,
        top_ips=top_ips,
    )

    return SecurityEventResponse(
        stats=stats,
        recent_events=SecurityEventList(events=events, total=total_events),
    )

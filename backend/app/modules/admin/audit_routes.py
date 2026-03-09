from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.permissions import Permission, require_permission
from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import User
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import String, and_, cast
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit-logs"])
logger = logging.getLogger(__name__)


class AuditLogItem(BaseModel):
    id: str
    event_type: str
    user_id: str | None = None
    user_email: str | None = None
    admin_id: str | None = None
    admin_email: str | None = None
    details: dict
    created_at: str


class AuditLogsResponse(BaseModel):
    logs: list[AuditLogItem]
    total: int
    page: int
    limit: int
    total_pages: int


def _parse_optional_uuid(raw_value: str | None, field_name: str) -> UUID | None:
    if not raw_value:
        return None
    try:
        return UUID(raw_value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}") from exc


def _parse_optional_datetime(raw_value: str | None, field_name: str) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name}. Use ISO format, e.g. 2026-03-09T00:00:00",
        ) from exc


def _build_audit_query(
    db: Session,
    *,
    event_type: str | None,
    user_id: str | None,
    admin_id: str | None,
    start_date: str | None,
    end_date: str | None,
    search: str | None,
):
    query = db.query(AuditLog)

    filters = []
    if event_type:
        try:
            filters.append(AuditLog.event_type == AuditEventType(event_type))
        except ValueError as exc:
            valid = [item.value for item in AuditEventType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type: {event_type}. Valid values: {valid}",
            ) from exc

    parsed_user_id = _parse_optional_uuid(user_id, "user_id")
    if parsed_user_id is not None:
        filters.append(AuditLog.user_id == parsed_user_id)

    parsed_admin_id = _parse_optional_uuid(admin_id, "admin_id")
    if parsed_admin_id is not None:
        filters.append(AuditLog.admin_id == parsed_admin_id)

    parsed_start = _parse_optional_datetime(start_date, "start_date")
    if parsed_start is not None:
        filters.append(AuditLog.created_at >= parsed_start)

    parsed_end = _parse_optional_datetime(end_date, "end_date")
    if parsed_end is not None:
        filters.append(AuditLog.created_at <= parsed_end)

    if search:
        filters.append(cast(AuditLog.details, String).ilike(f"%{search}%"))

    if filters:
        query = query.filter(and_(*filters))

    return query


def _resolve_user_email_maps(
    db: Session, logs: list[AuditLog]
) -> tuple[dict[str, str], dict[str, str]]:
    user_ids = {str(log.user_id) for log in logs if log.user_id}
    admin_ids = {str(log.admin_id) for log in logs if log.admin_id}
    related_ids = user_ids | admin_ids
    if not related_ids:
        return {}, {}

    users = db.query(User).filter(cast(User.id, String).in_(sorted(related_ids))).all()
    email_by_id = {str(user.id): user.email for user in users}
    return (
        {user_id: email_by_id[user_id] for user_id in user_ids if user_id in email_by_id},
        {admin_id: email_by_id[admin_id] for admin_id in admin_ids if admin_id in email_by_id},
    )


def _serialize_audit_log(
    log: AuditLog, user_email_map: dict[str, str], admin_email_map: dict[str, str]
) -> AuditLogItem:
    user_key = str(log.user_id) if log.user_id else None
    admin_key = str(log.admin_id) if log.admin_id else None
    return AuditLogItem(
        id=str(log.id),
        event_type=log.event_type.value,
        user_id=user_key,
        user_email=user_email_map.get(user_key) if user_key else None,
        admin_id=admin_key,
        admin_email=admin_email_map.get(admin_key) if admin_key else None,
        details=log.details or {},
        created_at=log.created_at.isoformat(),
    )


@router.get("", response_model=AuditLogsResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    admin_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
    db: Session = Depends(get_db),
):
    query = _build_audit_query(
        db,
        event_type=event_type,
        user_id=user_id,
        admin_id=admin_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )
    total = query.count()
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    user_email_map, admin_email_map = _resolve_user_email_maps(db, logs)
    logger.info("Admin %s viewed audit logs page=%s total=%s", current_user.email, page, total)
    return AuditLogsResponse(
        logs=[_serialize_audit_log(log, user_email_map, admin_email_map) for log in logs],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/event-types")
async def get_audit_event_types(
    _: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    return {"event_types": [event.value for event in AuditEventType]}


@router.get("/export")
async def export_audit_logs_csv(
    event_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    admin_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    _: User = Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
    db: Session = Depends(get_db),
):
    logs = (
        _build_audit_query(
            db,
            event_type=event_type,
            user_id=user_id,
            admin_id=admin_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )
        .order_by(AuditLog.created_at.desc())
        .all()
    )
    user_email_map, admin_email_map = _resolve_user_email_maps(db, logs)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "event_type",
            "user_id",
            "user_email",
            "admin_id",
            "admin_email",
            "details",
            "created_at",
        ]
    )
    for log in logs:
        user_key = str(log.user_id) if log.user_id else None
        admin_key = str(log.admin_id) if log.admin_id else None
        writer.writerow(
            [
                str(log.id),
                log.event_type.value,
                user_key or "",
                user_email_map.get(user_key, "") if user_key else "",
                admin_key or "",
                admin_email_map.get(admin_key, "") if admin_key else "",
                json.dumps(log.details or {}, ensure_ascii=True),
                log.created_at.isoformat(),
            ]
        )
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-logs.csv"},
    )

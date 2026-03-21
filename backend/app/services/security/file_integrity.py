from __future__ import annotations

import asyncio
import logging
import threading
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from app.core.config import settings
from app.core.security import calculate_file_hash, verify_file_integrity
from app.core.storage import storage
from app.modules.security.models import (
    FileIntegrity,
    SecurityEvent,
    SecurityEventType,
    Severity,
    VerificationStatus,
)
from app.services.email import send_email
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, Any] = {}
    error: dict[str, BaseException] = {}

    def runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as exc:  # pragma: no cover - defensive bridge
            error["value"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "value" in error:
        raise error["value"]

    return result.get("value")


def _admin_emails() -> list[str]:
    return [email.strip() for email in settings.ADMIN_EMAILS.split(",") if email.strip()]


def _parse_storage_location(file_url: str) -> tuple[str, str]:
    parsed = urlparse(file_url)
    path_parts = [part for part in parsed.path.split("/") if part]
    public_marker = ["storage", "v1", "object", "public"]

    for index in range(len(path_parts) - len(public_marker)):
        if path_parts[index : index + len(public_marker)] == public_marker:
            bucket_index = index + len(public_marker)
            if bucket_index >= len(path_parts):
                break
            bucket = path_parts[bucket_index]
            file_path = "/".join(path_parts[bucket_index + 1 :])
            if file_path:
                return bucket, file_path

    fallback_bucket = settings.SUPABASE_STORAGE_KYC_BUCKET
    marker = f"/{fallback_bucket}/"
    if marker in parsed.path:
        _, file_path = parsed.path.split(marker, 1)
        if file_path:
            return fallback_bucket, file_path

    raise ValueError(f"Unable to determine storage bucket/path from URL: {file_url}")


class FileIntegrityService:
    @staticmethod
    def calculate_sha256(file_bytes: bytes) -> str:
        return calculate_file_hash(file_bytes)

    @staticmethod
    def create_integrity_record(
        db: Session,
        *,
        file_url: str,
        file_name: str,
        file_bytes: bytes,
        mime_type: str,
        uploaded_by_id: str,
    ) -> FileIntegrity:
        integrity = db.query(FileIntegrity).filter(FileIntegrity.file_url == file_url).first()
        if integrity is None:
            integrity = FileIntegrity(file_url=file_url)
            db.add(integrity)

        integrity.file_name = file_name
        integrity.file_size = len(file_bytes)
        integrity.mime_type = mime_type
        integrity.sha256_hash = FileIntegrityService.calculate_sha256(file_bytes)
        integrity.uploaded_by = UUID(uploaded_by_id)
        integrity.verification_status = VerificationStatus.VERIFIED
        integrity.verification_error = None
        integrity.last_verified = None
        integrity.tampering_detected = False
        integrity.tampering_detected_at = None
        return integrity

    @staticmethod
    def verify_record(db: Session, integrity_record: FileIntegrity) -> tuple[bool, str | None]:
        try:
            bucket, file_path = _parse_storage_location(integrity_record.file_url)
            file_bytes = _run_async(storage.download_file(bucket, file_path))
            if not file_bytes:
                error = "File download returned no content"
                FileIntegrityService._mark_failed(integrity_record, error)
                db.commit()
                return False, error

            integrity_record.last_verified = datetime.now(UTC)

            if verify_file_integrity(file_bytes, integrity_record.sha256_hash):
                integrity_record.verification_status = VerificationStatus.VERIFIED
                integrity_record.verification_error = None
                integrity_record.tampering_detected = False
                integrity_record.tampering_detected_at = None
                db.commit()
                return True, None

            error = "Hash mismatch - file may have been tampered with"
            integrity_record.verification_status = VerificationStatus.TAMPERED
            integrity_record.verification_error = error
            integrity_record.tampering_detected = True
            integrity_record.tampering_detected_at = datetime.now(UTC)
            FileIntegrityService._create_tampering_event(db, integrity_record)
            db.commit()
            FileIntegrityService._send_tampering_alert(integrity_record)
            return False, error
        except Exception as exc:
            error = f"Verification error: {exc}"
            FileIntegrityService._mark_failed(integrity_record, error)
            db.commit()
            return False, error

    @staticmethod
    def verify_all_files(db: Session) -> dict[str, Any]:
        records = db.query(FileIntegrity).order_by(FileIntegrity.created_at.asc()).all()
        stats: dict[str, Any] = {
            "total": len(records),
            "valid": 0,
            "invalid": 0,
            "errors": 0,
            "tampering_detected": [],
        }

        for record in records:
            is_valid, error = FileIntegrityService.verify_record(db, record)
            if is_valid:
                stats["valid"] += 1
                continue

            if record.verification_status == VerificationStatus.TAMPERED:
                stats["invalid"] += 1
                stats["tampering_detected"].append(
                    {
                        "id": str(record.id),
                        "file_name": record.file_name,
                        "file_url": record.file_url,
                        "detected_at": (
                            record.tampering_detected_at.isoformat()
                            if record.tampering_detected_at
                            else None
                        ),
                    }
                )
            else:
                stats["errors"] += 1
                if error:
                    logger.warning(
                        "File integrity verification failed for %s: %s", record.file_url, error
                    )

        return stats

    @staticmethod
    def _mark_failed(integrity_record: FileIntegrity, error: str) -> None:
        integrity_record.verification_status = VerificationStatus.FAILED
        integrity_record.verification_error = error
        integrity_record.last_verified = datetime.now(UTC)

    @staticmethod
    def _create_tampering_event(db: Session, integrity_record: FileIntegrity) -> None:
        event = SecurityEvent(
            event_type=SecurityEventType.FILE_TAMPERING,
            severity=Severity.CRITICAL,
            user_id=integrity_record.uploaded_by,
            details={
                "file_integrity_id": str(integrity_record.id),
                "file_name": integrity_record.file_name,
                "file_url": integrity_record.file_url,
                "stored_hash": integrity_record.sha256_hash,
                "verification_error": integrity_record.verification_error,
            },
        )
        db.add(event)

    @staticmethod
    def _send_tampering_alert(integrity_record: FileIntegrity) -> None:
        subject = f"[Security] File tampering detected: {integrity_record.file_name}"
        text_content = (
            "A file integrity verification failed.\n"
            f"File: {integrity_record.file_name}\n"
            f"URL: {integrity_record.file_url}\n"
            f"Uploaded by: {integrity_record.uploaded_by}\n"
            f"Detected at: {integrity_record.tampering_detected_at}\n"
            f"Error: {integrity_record.verification_error}"
        )
        html_content = (
            "<p>A file integrity verification failed.</p>"
            f"<p><strong>File:</strong> {integrity_record.file_name}<br>"
            f"<strong>URL:</strong> {integrity_record.file_url}<br>"
            f"<strong>Uploaded by:</strong> {integrity_record.uploaded_by}<br>"
            f"<strong>Detected at:</strong> {integrity_record.tampering_detected_at}<br>"
            f"<strong>Error:</strong> {integrity_record.verification_error}</p>"
        )

        for admin_email in _admin_emails():
            try:
                sent = bool(
                    _run_async(send_email(admin_email, subject, html_content, text_content))
                )
                if not sent:
                    logger.warning(
                        "Tampering alert email failed for %s and file %s",
                        admin_email,
                        integrity_record.file_url,
                    )
            except Exception:
                logger.exception(
                    "Tampering alert dispatch crashed for %s and file %s",
                    admin_email,
                    integrity_record.file_url,
                )


file_integrity_service = FileIntegrityService()

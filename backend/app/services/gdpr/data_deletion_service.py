"""
GDPR data deletion service.

Story: CD-103
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

from app.core.config import settings
from app.core.redis import blacklist_token, delete_all_user_sessions, get_user_sessions
from app.core.storage import storage
from app.models.audit_log import AuditEventType, AuditLog
from app.modules.auth.models import Session as UserSession
from app.modules.auth.models import User
from app.modules.gdpr.models import GDPRDeletion, GDPRDeletionStatus
from app.modules.kyc.models import KYCDocument
from app.modules.orders.models import Order, OrderStatus
from app.modules.payments.models import Payment, PaymentStatus
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


ACTIVE_ORDER_STATUSES = tuple(
    status for status in OrderStatus if status not in {OrderStatus.DELIVERED, OrderStatus.CANCELLED}
)
PENDING_PAYMENT_STATUSES = (PaymentStatus.PENDING, PaymentStatus.PROCESSING)


@dataclass
class DeletionBlocker:
    blocked: bool
    reason: str = ""


class DataDeletionService:
    """Orchestrate GDPR deletion checks and anonymization workflow."""

    @staticmethod
    def check_deletion_blockers(user: User, db: Session) -> DeletionBlocker:
        active_orders = (
            db.query(Order)
            .filter(Order.user_id == user.id, Order.status.in_(ACTIVE_ORDER_STATUSES))
            .count()
        )
        if active_orders > 0:
            return DeletionBlocker(
                blocked=True,
                reason=(
                    f"Cannot delete account while {active_orders} active order(s) exist. "
                    "Complete or cancel active orders first."
                ),
            )

        pending_payments = (
            db.query(Payment)
            .filter(Payment.user_id == user.id, Payment.status.in_(PENDING_PAYMENT_STATUSES))
            .count()
        )
        if pending_payments > 0:
            return DeletionBlocker(
                blocked=True,
                reason=(
                    f"Cannot delete account while {pending_payments} pending payment(s) exist. "
                    "Wait until payments are completed or failed."
                ),
            )

        return DeletionBlocker(blocked=False)

    @staticmethod
    def anonymize_user_data(user: User) -> dict[str, str | None]:
        original_data = {"email": user.email, "name": user.name}
        anon_id = secrets.token_hex(8)

        user.email = f"deleted_{anon_id}@cleardrive.lk"
        user.name = f"Deleted User {anon_id}"
        user.phone = None
        user.password_hash = secrets.token_hex(32)
        user.google_id = None
        user.deleted_at = datetime.now(UTC)

        return original_data

    @staticmethod
    def _extract_file_path_from_public_url(url: str, bucket: str) -> str:
        parsed = urlparse(url)
        marker = f"/storage/v1/object/public/{bucket}/"
        if marker in parsed.path:
            return parsed.path.split(marker, 1)[1]
        return parsed.path.lstrip("/") or url

    @staticmethod
    async def delete_kyc_documents(user: User, db: Session) -> int:
        kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user.id).first()
        if not kyc:
            return 0

        deleted_count = 0
        for url in [kyc.nic_front_url, kyc.nic_back_url, kyc.selfie_url]:
            if not url:
                continue
            try:
                file_path = DataDeletionService._extract_file_path_from_public_url(
                    url, settings.SUPABASE_STORAGE_KYC_BUCKET
                )
                await storage.delete_file(settings.SUPABASE_STORAGE_KYC_BUCKET, file_path)
                deleted_count += 1
            except Exception:
                logger.exception("Failed to delete KYC file for user_id=%s", user.id)

        # Keep DB constraints intact while removing personal payloads.
        kyc.nic_front_url = ""
        kyc.nic_back_url = ""
        kyc.selfie_url = ""
        kyc.nic_number = None
        kyc.full_name = None
        kyc.date_of_birth = None
        kyc.address = None
        kyc.gender = None
        kyc.user_provided_data = None
        kyc.extracted_data = None
        kyc.discrepancies = None
        kyc.rejection_reason = None

        return deleted_count

    @staticmethod
    async def revoke_all_sessions(user: User, db: Session) -> None:
        redis_sessions = await get_user_sessions(str(user.id))
        for session in redis_sessions:
            token_jti = session.get("token_jti")
            if token_jti:
                await blacklist_token(token_jti, 30 * 24 * 60 * 60)

        await delete_all_user_sessions(str(user.id))

        (
            db.query(UserSession)
            .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
            .update({"is_active": False}, synchronize_session=False)
        )

    @staticmethod
    async def process_deletion(
        *,
        user: User,
        ip_address: str,
        user_agent: str,
        db: Session,
    ) -> tuple[bool, str, GDPRDeletion]:
        deletion = GDPRDeletion(
            user_id=user.id,
            status=GDPRDeletionStatus.PROCESSING,
            ip_address=ip_address,
            user_agent=user_agent,
            original_email=user.email,
            original_name=user.name,
        )
        db.add(deletion)
        db.flush()

        db.add(
            AuditLog(
                event_type=AuditEventType.GDPR_DELETION_REQUESTED,
                user_id=user.id,
                admin_id=None,
                details={"gdpr_deletion_id": str(deletion.id)},
            )
        )

        blocker = DataDeletionService.check_deletion_blockers(user, db)
        if blocker.blocked:
            deletion.status = GDPRDeletionStatus.REJECTED
            deletion.rejection_reason = blocker.reason
            deletion.processed_at = datetime.now(UTC)
            db.add(
                AuditLog(
                    event_type=AuditEventType.GDPR_DELETION_REJECTED,
                    user_id=user.id,
                    admin_id=None,
                    details={
                        "gdpr_deletion_id": str(deletion.id),
                        "reason": blocker.reason,
                    },
                )
            )
            db.commit()
            return (False, blocker.reason, deletion)

        try:
            DataDeletionService.anonymize_user_data(user)
            deletion.data_anonymized = True

            deleted_docs = await DataDeletionService.delete_kyc_documents(user, db)
            deletion.kyc_deleted = deleted_docs > 0

            await DataDeletionService.revoke_all_sessions(user, db)
            deletion.sessions_revoked = True

            deletion.status = GDPRDeletionStatus.COMPLETED
            deletion.processed_at = datetime.now(UTC)

            db.add(
                AuditLog(
                    event_type=AuditEventType.GDPR_DELETION_COMPLETED,
                    user_id=user.id,
                    admin_id=None,
                    details={
                        "gdpr_deletion_id": str(deletion.id),
                        "kyc_files_deleted_count": deleted_docs,
                    },
                )
            )
            db.commit()
            return (True, "Your account has been successfully deleted", deletion)
        except Exception as exc:
            logger.exception("GDPR deletion failed for user_id=%s", user.id)
            deletion.status = GDPRDeletionStatus.REJECTED
            deletion.rejection_reason = "Technical error while processing deletion request"
            deletion.processed_at = datetime.now(UTC)
            db.add(
                AuditLog(
                    event_type=AuditEventType.GDPR_DELETION_REJECTED,
                    user_id=user.id,
                    admin_id=None,
                    details={
                        "gdpr_deletion_id": str(deletion.id),
                        "reason": str(exc),
                    },
                )
            )
            db.commit()
            return (False, "Deletion failed due to a technical error", deletion)


data_deletion_service = DataDeletionService()

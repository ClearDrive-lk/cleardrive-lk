"""
GDPR data export service.
Story: CD-102.2, CD-102.3
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.modules.auth.models import Session, User
from app.modules.kyc.models import KYCDocument
from app.modules.notifications.models import EmailLog
from app.modules.orders.models import Order
from app.modules.payments.models import Payment
from app.modules.shipping.models import ShipmentDetails
from sqlalchemy.orm import Session as OrmSession

logger = logging.getLogger(__name__)


def _dt(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _enum(value: Any) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _decimal(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


class DataExportService:
    """Collect and export all user data per GDPR Article 15."""

    @staticmethod
    def collect_user_data(user: User, db: OrmSession) -> dict[str, Any]:
        logger.info("GDPR export data collection started for user=%s", user.id)

        orders = DataExportService._collect_orders(user, db)
        kyc_documents = DataExportService._collect_kyc(user, db)
        payments = DataExportService._collect_payments(user, db)
        shipments = DataExportService._collect_shipments(user, db)
        email_communications = DataExportService._collect_emails(user, db)
        login_sessions = DataExportService._collect_sessions(user, db)

        data = {
            "export_metadata": {
                "export_date": _dt(datetime.utcnow()),
                "format": "JSON",
                "gdpr_article": "Article 15 - Right of Access",
                "user_id": str(user.id),
            },
            "user_profile": DataExportService._collect_profile(user),
            "orders": orders,
            "kyc_documents": kyc_documents,
            "payments": payments,
            "shipments": shipments,
            "email_communications": email_communications,
            "login_sessions": login_sessions,
        }

        data["statistics"] = {
            "total_orders": len(orders),
            "total_payments": len(payments),
            "total_emails": len(email_communications),
            "account_created": _dt(user.created_at),
            "account_updated": _dt(user.updated_at),
        }

        logger.info(
            "GDPR export data collection complete for user=%s (orders=%s, payments=%s)",
            user.id,
            len(orders),
            len(payments),
        )
        return data

    @staticmethod
    def _collect_profile(user: User) -> dict[str, Any]:
        return {
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "role": _enum(user.role),
            "deleted_at": _dt(user.deleted_at),
            "created_at": _dt(user.created_at),
            "updated_at": _dt(user.updated_at),
        }

    @staticmethod
    def _collect_orders(user: User, db: OrmSession) -> list[dict[str, Any]]:
        orders = db.query(Order).filter(Order.user_id == user.id).all()
        results: list[dict[str, Any]] = []
        for order in orders:
            results.append(
                {
                    "order_id": str(order.id),
                    "status": _enum(order.status),
                    "payment_status": _enum(order.payment_status),
                    "total_cost_lkr": _decimal(order.total_cost_lkr),
                    "shipping_address": order.shipping_address,
                    "phone": order.phone,
                    "vehicle": {
                        "id": str(order.vehicle.id) if order.vehicle else None,
                        "make": order.vehicle.make if order.vehicle else None,
                        "model": order.vehicle.model if order.vehicle else None,
                        "year": order.vehicle.year if order.vehicle else None,
                        "stock_no": order.vehicle.stock_no if order.vehicle else None,
                    },
                    "created_at": _dt(order.created_at),
                    "updated_at": _dt(order.updated_at),
                }
            )
        return results

    @staticmethod
    def _collect_kyc(user: User, db: OrmSession) -> dict[str, Any] | None:
        kyc = db.query(KYCDocument).filter(KYCDocument.user_id == user.id).first()
        if not kyc:
            return None

        return {
            "status": _enum(kyc.status),
            "submitted_at": _dt(kyc.created_at),
            "reviewed_at": _dt(kyc.reviewed_at),
            "reviewed_by": str(kyc.reviewed_by) if kyc.reviewed_by else None,
            "rejection_reason": kyc.rejection_reason,
            "personal_data": {
                "nic_number": kyc.nic_number,
                "full_name": kyc.full_name,
                "date_of_birth": _dt(kyc.date_of_birth),
                "address": kyc.address,
                "gender": kyc.gender,
            },
            "documents": {
                "nic_front_url": kyc.nic_front_url,
                "nic_back_url": kyc.nic_back_url,
                "selfie_url": kyc.selfie_url,
            },
            "extraction": {
                "user_provided_data": kyc.user_provided_data,
                "extracted_data": kyc.extracted_data,
                "discrepancies": kyc.discrepancies,
            },
        }

    @staticmethod
    def _collect_payments(user: User, db: OrmSession) -> list[dict[str, Any]]:
        payments = db.query(Payment).filter(Payment.user_id == user.id).all()
        return [
            {
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "payhere_payment_id": payment.payhere_payment_id,
                "payhere_order_id": payment.payhere_order_id,
                "amount": _decimal(payment.amount),
                "currency": payment.currency,
                "status": _enum(payment.status),
                "payment_method": payment.payment_method,
                "card_holder_name": payment.card_holder_name,
                "card_no_last4": payment.card_no,
                "completed_at": _dt(payment.completed_at),
                "created_at": _dt(payment.created_at),
                "updated_at": _dt(payment.updated_at),
            }
            for payment in payments
        ]

    @staticmethod
    def _collect_shipments(user: User, db: OrmSession) -> list[dict[str, Any]]:
        shipments = db.query(ShipmentDetails).join(Order).filter(Order.user_id == user.id).all()
        return [
            {
                "shipment_id": str(shipment.id),
                "order_id": str(shipment.order_id),
                "exporter_id": str(shipment.exporter_id),
                "vessel_name": shipment.vessel_name,
                "voyage_number": shipment.voyage_number,
                "departure_port": shipment.departure_port,
                "arrival_port": shipment.arrival_port,
                "departure_date": _dt(shipment.departure_date),
                "estimated_departure_date": _dt(shipment.estimated_departure_date),
                "actual_departure_date": _dt(shipment.actual_departure_date),
                "estimated_arrival_date": _dt(shipment.estimated_arrival_date),
                "actual_arrival_date": _dt(shipment.actual_arrival_date),
                "container_number": shipment.container_number,
                "bill_of_landing_number": shipment.bill_of_landing_number,
                "seal_number": shipment.seal_number,
                "tracking_number": shipment.tracking_number,
                "status": _enum(shipment.status),
                "submitted_at": _dt(shipment.submitted_at),
                "admin_approved_at": _dt(shipment.admin_approved_at),
                "admin_approved_by": (
                    str(shipment.admin_approved_by) if shipment.admin_approved_by else None
                ),
                "documents_uploaded": shipment.documents_uploaded,
                "approved": shipment.approved,
                "created_at": _dt(shipment.created_at),
                "updated_at": _dt(shipment.updated_at),
            }
            for shipment in shipments
        ]

    @staticmethod
    def _collect_emails(user: User, db: OrmSession) -> list[dict[str, Any]]:
        emails = (
            db.query(EmailLog)
            .filter(EmailLog.to_email == user.email)
            .order_by(EmailLog.created_at.desc())
            .limit(100)
            .all()
        )
        return [
            {
                "email_id": str(email.id),
                "to_email": email.to_email,
                "from_email": email.from_email,
                "subject": email.subject,
                "template_name": email.template_name,
                "status": _enum(email.status),
                "sent_at": _dt(email.sent_at),
                "failed_at": _dt(email.failed_at),
                "error_message": email.error_message,
                "created_at": _dt(email.created_at),
            }
            for email in emails
        ]

    @staticmethod
    def _collect_sessions(user: User, db: OrmSession) -> list[dict[str, Any]]:
        sessions = db.query(Session).filter(Session.user_id == user.id).all()
        return [
            {
                "session_id": str(session.id),
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "device_info": session.device_info,
                "location": session.location,
                "is_active": session.is_active,
                "expires_at": _dt(session.expires_at),
                "last_active": _dt(session.last_active),
                "created_at": _dt(session.created_at),
                "updated_at": _dt(session.updated_at),
            }
            for session in sessions
        ]

    @staticmethod
    def generate_json_export(data: dict[str, Any]) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)


data_export_service = DataExportService()

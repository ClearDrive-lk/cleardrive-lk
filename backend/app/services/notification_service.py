import logging
from typing import Optional

from app.core.config import settings
from app.services.email import send_otp_email as base_send_otp_email
from app.services.email import template_env
from app.services.email_queue import email_queue

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service to handle high-level transactional emails and notifications.
    CD-121 - Transactional Emails
    """

    def __init__(self):
        # Determine the frontend URL for email links
        if settings.BACKEND_CORS_ORIGINS:
            self.frontend_url = settings.BACKEND_CORS_ORIGINS[0]
        else:
            self.frontend_url = "http://localhost:3000"

    async def send_otp_email(self, email: str, otp: str, name: Optional[str] = None) -> bool:
        """
        CD-121.1 - Send OTP email.
        OTP is sent immediately without the queue for lowest latency.
        """
        return await base_send_otp_email(email, otp, name)

    async def _enqueue_template(
        self, to_email: str, subject: str, template_name: str, context: dict, priority: int = 5
    ) -> str:
        """Helper to render Jinja template and enqueue the email."""
        context["frontend_url"] = self.frontend_url
        context["subject"] = subject

        try:
            template = template_env.get_template(template_name)
            html_content = template.render(**context)

            # A simple text fallback instructing the user to view in HTML
            text_content = (
                f"Please view this email in an HTML-compatible client. Link: {self.frontend_url}"
            )

            email_id = await email_queue.enqueue(
                to_email=to_email,
                subject=subject,
                html_body=html_content,
                text_body=text_content,
                priority=priority,
                template_name=template_name,
                template_data=context,
            )
            logger.info(f"Successfully enqueued {template_name} to {to_email} with ID {email_id}")
            return email_id
        except Exception as e:
            logger.error(f"Failed to enqueue email {template_name} to {to_email}: {str(e)}")
            return ""

    async def send_order_confirmation(
        self,
        email: str,
        user_name: str,
        order_id: str,
        vehicle_name: str,
        chassis_no: str,
        total_price: str,
    ) -> str:
        """CD-121.2 - Send Order Confirmation."""
        return await self._enqueue_template(
            to_email=email,
            subject=f"Order Confirmation #{order_id}",
            template_name="order_confirmation.html",
            context={
                "user_name": user_name,
                "order_id": order_id,
                "vehicle_name": vehicle_name,
                "chassis_no": chassis_no,
                "total_price": total_price,
            },
            priority=2,  # Higher priority for order confirmation
        )

    async def send_payment_confirmation(
        self,
        email: str,
        user_name: str,
        order_id: str,
        amount: str,
        receipt_id: str,
        payment_date: str,
        payment_method: str,
    ) -> str:
        """CD-121.3 - Send Payment Confirmation."""
        return await self._enqueue_template(
            to_email=email,
            subject=f"Payment Received for Order #{order_id}",
            template_name="payment_confirmation.html",
            context={
                "user_name": user_name,
                "order_id": order_id,
                "amount": amount,
                "receipt_id": receipt_id,
                "payment_date": payment_date,
                "payment_method": payment_method,
            },
            priority=3,
        )

    async def send_kyc_approved(self, email: str, user_name: str) -> str:
        """CD-121.4 - Send KYC Approval Notification."""
        return await self._enqueue_template(
            to_email=email,
            subject="KYC Verification Approved",
            template_name="kyc_approved.html",
            context={"user_name": user_name},
            priority=4,
        )

    async def send_kyc_rejected(self, email: str, user_name: str, rejection_reason: str) -> str:
        """CD-121.4 - Send KYC Rejection Notification."""
        return await self._enqueue_template(
            to_email=email,
            subject="Action Required: KYC Verification Update",
            template_name="kyc_rejected.html",
            context={"user_name": user_name, "rejection_reason": rejection_reason},
            priority=4,
        )

    async def send_shipment_notification(
        self,
        email: str,
        user_name: str,
        order_id: str,
        vessel_name: str,
        tracking_number: str,
        estimated_arrival: str,
    ) -> str:
        """CD-121.5 - Send Shipment Notification."""
        return await self._enqueue_template(
            to_email=email,
            subject=f"Shipment Update for Order #{order_id}",
            template_name="shipment_notification.html",
            context={
                "user_name": user_name,
                "order_id": order_id,
                "vessel_name": vessel_name,
                "tracking_number": tracking_number,
                "estimated_arrival": estimated_arrival,
            },
            priority=5,
        )

    async def send_status_change(
        self,
        email: str,
        user_name: str,
        order_id: str,
        new_status: str,
        status_message: Optional[str] = None,
    ) -> str:
        """CD-121.6 - Send Status Change Updates."""
        return await self._enqueue_template(
            to_email=email,
            subject=f"Status Update for Order #{order_id}",
            template_name="status_change.html",
            context={
                "user_name": user_name,
                "order_id": order_id,
                "new_status": new_status,
                "status_message": status_message,
            },
            priority=5,
        )


# Global instance
notification_service = NotificationService()

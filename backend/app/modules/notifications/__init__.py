"""Notifications module for email and push notifications"""

from .service import email_service, send_otp_email, send_order_confirmation_email
from .queue import email_queue
from .worker import email_queue_worker, start_email_worker, stop_email_worker
from .models import EmailLog, EmailStatus
from .schemas import EmailRequest, EmailResponse, EmailTemplate

__all__ = [
    "email_service",
    "send_otp_email",
    "send_order_confirmation_email",
    "email_queue",
    "email_queue_worker",
    "start_email_worker",
    "stop_email_worker",
    "EmailLog",
    "EmailStatus",
    "EmailRequest",
    "EmailResponse",
    "EmailTemplate",
]
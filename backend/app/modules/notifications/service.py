# backend/app/modules/notifications/service.py

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Optional, Dict, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.modules.notifications.models import EmailLog, EmailStatus
from backend.app.modules.notifications.schemas import EmailRequest, EmailResponse, EmailTemplate
from backend.app.modules.notifications.templates import template_engine
from backend.app.modules.notifications.queue import email_queue

logger = logging.getLogger(__name__)


class EmailService:
    """Core email service with SMTP integration"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = formataddr(("ClearDrive.lk", settings.SMTP_USERNAME))
        
        logger.info(f"Email service initialized with SMTP: {self.smtp_host}:{self.smtp_port}")
    
    async def send_email_async(
        self,
        recipient_email: str,
        recipient_name: Optional[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send email asynchronously via SMTP
        
        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's name
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.from_email
            message['To'] = formataddr((recipient_name or recipient_email, recipient_email))
            message['Subject'] = subject
            
            # Add text content (fallback)
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Connect and send
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=False,  # We'll use STARTTLS
            ) as smtp:
                await smtp.connect()
                await smtp.starttls()  # Upgrade to TLS
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(message)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return (True, None)
            
        except aiosmtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(f"Failed to send email to {recipient_email}: {error_msg}")
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to send email to {recipient_email}: {error_msg}")
            return (False, error_msg)
    
    async def send_templated_email(
        self,
        db: Session,
        email_request: EmailRequest,
        user_id: Optional[int] = None,
        queue_email: bool = True
    ) -> EmailResponse:
        """
        Send email using a template (main entry point)
        
        Args:
            db: Database session
            email_request: Email request data
            user_id: User ID (for rate limiting)
            queue_email: If True, queue email instead of sending immediately
        
        Returns:
            EmailResponse with status
        """
        try:
            # Rate limiting check
            if user_id and not email_queue.check_rate_limit(user_id, max_per_hour=10):
                return EmailResponse(
                    success=False,
                    message="Rate limit exceeded. Maximum 10 emails per hour.",
                    queued=False
                )
            
            # Render template
            html_content = template_engine.render_template(
                template_name=email_request.template.value,
                context=email_request.template_data,
                recipient_email=email_request.recipient_email,
                recipient_name=email_request.recipient_name
            )
            
            text_content = template_engine.render_text_version(
                template_name=email_request.template.value,
                context=email_request.template_data
            )
            
            # Create email log entry
            email_log = EmailLog(
                recipient_email=email_request.recipient_email,
                recipient_name=email_request.recipient_name,
                subject=email_request.subject,
                template_name=email_request.template.value,
                status=EmailStatus.QUEUED if queue_email else EmailStatus.PENDING,
                template_data_summary=self._create_summary(email_request.template_data),
            )
            db.add(email_log)
            db.commit()
            db.refresh(email_log)
            
            if queue_email:
                # Add to queue
                queued = email_queue.enqueue(
                    email_log_id=email_log.id,
                    recipient_email=email_request.recipient_email,
                    subject=email_request.subject,
                    html_content=html_content,
                    text_content=text_content,
                    priority=email_request.priority.value
                )
                
                if not queued:
                    email_log.status = EmailStatus.FAILED
                    email_log.error_message = "Failed to enqueue email"
                    db.commit()
                    
                    return EmailResponse(
                        success=False,
                        message="Failed to queue email",
                        email_log_id=email_log.id,
                        queued=False
                    )
                
                return EmailResponse(
                    success=True,
                    message="Email queued successfully",
                    email_log_id=email_log.id,
                    queued=True
                )
            
            else:
                # Send immediately
                email_log.status = EmailStatus.SENDING
                email_log.attempts = 1
                email_log.last_attempt_at = datetime.utcnow()
                db.commit()
                
                success, error_message = await self.send_email_async(
                    recipient_email=email_request.recipient_email,
                    recipient_name=email_request.recipient_name,
                    subject=email_request.subject,
                    html_content=html_content,
                    text_content=text_content
                )
                
                if success:
                    email_log.status = EmailStatus.SENT
                    email_log.sent_at = datetime.utcnow()
                    email_log.delivered = True
                else:
                    email_log.status = EmailStatus.FAILED
                    email_log.error_message = error_message
                
                db.commit()
                
                return EmailResponse(
                    success=success,
                    message="Email sent successfully" if success else f"Failed to send: {error_message}",
                    email_log_id=email_log.id,
                    queued=False
                )
            
        except ValueError as e:
            # Template not found or validation error
            logger.error(f"Email validation error: {str(e)}")
            return EmailResponse(
                success=False,
                message=str(e),
                queued=False
            )
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return EmailResponse(
                success=False,
                message="Internal server error",
                queued=False
            )
    
    async def process_queue_item(self, db: Session, email_data: Dict[str, Any]) -> bool:
        """
        Process a single email from the queue
        
        Args:
            db: Database session
            email_data: Email data from queue
        
        Returns:
            True if sent successfully
        """
        email_log_id = email_data['email_log_id']
        
        try:
            # Get email log from database
            email_log = db.query(EmailLog).filter(EmailLog.id == email_log_id).first()
            
            if not email_log:
                logger.error(f"Email log {email_log_id} not found in database")
                return False
            
            # Update status
            email_log.status = EmailStatus.SENDING
            email_log.attempts += 1
            email_log.last_attempt_at = datetime.utcnow()
            db.commit()
            
            # Send email
            success, error_message = await self.send_email_async(
                recipient_email=email_data['recipient_email'],
                recipient_name=email_data.get('recipient_name'),
                subject=email_data['subject'],
                html_content=email_data['html_content'],
                text_content=email_data.get('text_content', '')
            )
            
            if success:
                # Mark as sent
                email_log.status = EmailStatus.SENT
                email_log.sent_at = datetime.utcnow()
                email_log.delivered = True
                db.commit()
                
                # Mark in queue
                email_queue.mark_sent(email_log_id)
                
                return True
            else:
                # Mark as failed
                email_log.status = EmailStatus.FAILED if email_log.attempts >= email_log.max_attempts else EmailStatus.RETRY
                email_log.error_message = error_message
                db.commit()
                
                # Handle retry in queue
                email_queue.mark_failed(
                    email_log_id=email_log_id,
                    email_data=email_data,
                    error_message=error_message,
                    max_attempts=email_log.max_attempts
                )
                
                return False
            
        except Exception as e:
            logger.error(f"Error processing queue item {email_log_id}: {str(e)}")
            return False
    
    @staticmethod
    def _create_summary(template_data: Dict[str, Any]) -> str:
        """Create a summary of template data for logging (no sensitive data)"""
        # Don't log actual values, just keys
        safe_keys = ['order_id', 'vehicle_make', 'vehicle_model', 'template_type']
        summary = {k: v for k, v in template_data.items() if k in safe_keys}
        return str(summary)[:500]  # Limit length


# Singleton instance
email_service = EmailService()


# Helper functions for common email types
async def send_otp_email(
    db: Session,
    recipient_email: str,
    recipient_name: Optional[str],
    otp_code: str,
    expires_in_minutes: int = 5,
    user_id: Optional[int] = None
) -> EmailResponse:
    """Send OTP email"""
    email_request = EmailRequest(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        subject=f"Your ClearDrive.lk OTP: {otp_code}",
        template=EmailTemplate.OTP,
        template_data={
            "otp_code": otp_code,
            "expires_in_minutes": expires_in_minutes,
        },
        priority="HIGH"
    )
    
    return await email_service.send_templated_email(db, email_request, user_id, queue_email=False)


async def send_order_confirmation_email(
    db: Session,
    recipient_email: str,
    recipient_name: str,
    order_data: Dict[str, Any],
    user_id: Optional[int] = None
) -> EmailResponse:
    """Send order confirmation email"""
    email_request = EmailRequest(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        subject=f"Order Confirmed - {order_data['order_id']}",
        template=EmailTemplate.ORDER_CONFIRMATION,
        template_data=order_data,
        priority="NORMAL"
    )
    
    return await email_service.send_templated_email(db, email_request, user_id, queue_email=True)

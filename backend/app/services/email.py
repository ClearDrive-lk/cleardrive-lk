# backend/app/services/email.py
"""
Email service for sending OTPs and notifications.
"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import logging
from typing import Optional


from app.core.config import settings

logger = logging.getLogger(__name__)

# Jinja2 template environment
template_env = Environment(
    loader=FileSystemLoader("app/templates/email")
)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send email via SMTP.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text fallback (optional)
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Add text part if provided
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)
        
        # Add HTML part
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_otp_email(email: str, otp: str, name: Optional[str] = None) -> bool:
    """
    Send OTP verification email.
    
    Args:
        email: User's email
        otp: 6-digit OTP
        name: User's name (optional)
    
    Returns:
        True if sent successfully
    """
    # Render template
    template = template_env.get_template("otp_email.html")
    html_content = template.render(
        otp=otp,
        name=name or "User",
        expiry_minutes=settings.OTP_EXPIRY_MINUTES
    )
    
    # Plain text fallback
    text_content = f"""
Hello {name or 'User'},

Your ClearDrive.lk verification code is: {otp}

This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Best regards,
ClearDrive.lk Team
    """.strip()
    
    # Send email
    return await send_email(
        to_email=email,
        subject="Your ClearDrive.lk Verification Code",
        html_content=html_content,
        text_content=text_content
    )
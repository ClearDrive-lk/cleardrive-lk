# backend/app/services/email.py
"""
Email service for sending OTPs and notifications.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
import httpx
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Jinja2 template environment
template_env = Environment(
    loader=FileSystemLoader("app/templates/email"),
    autoescape=select_autoescape(["html", "xml"]),
)


async def _send_email_via_resend_api(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """Send email via Resend HTTPS API (fallback when SMTP is unavailable)."""
    api_key = settings.RESEND_API_KEY or settings.SMTP_PASSWORD
    if not api_key:
        return False

    from_email = settings.RESEND_FROM_EMAIL or settings.SMTP_FROM_EMAIL
    payload = {
        "from": f"{settings.SMTP_FROM_NAME} <{from_email}>",
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }
    if text_content:
        payload["text"] = text_content

    try:
        async with httpx.AsyncClient(timeout=settings.SMTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if 200 <= response.status_code < 300:
            logger.info(f"Email sent successfully to {to_email} via Resend API")
            return True

        # If sender domain is not verified in Resend, retry once with sandbox sender.
        if response.status_code == 403 and from_email != "onboarding@resend.dev":
            sandbox_payload = dict(payload)
            sandbox_payload["from"] = f"{settings.SMTP_FROM_NAME} <onboarding@resend.dev>"
            async with httpx.AsyncClient(timeout=settings.SMTP_TIMEOUT_SECONDS) as client:
                sandbox_response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=sandbox_payload,
                )
            if 200 <= sandbox_response.status_code < 300:
                logger.warning(
                    "Primary sender domain rejected by Resend; sent via onboarding@resend.dev "
                    "to %s",
                    to_email,
                )
                return True

        logger.error(
            "Failed to send email to %s via Resend API: status=%s body=%s",
            to_email,
            response.status_code,
            response.text,
        )
        return False
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via Resend API: {str(e)}")
        return False


async def send_email(
    to_email: str, subject: str, html_content: str, text_content: Optional[str] = None
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
    # Prefer HTTPS API when a Resend API key is configured to avoid blocked SMTP ports.
    if settings.RESEND_API_KEY:
        if await _send_email_via_resend_api(to_email, subject, html_content, text_content):
            return True

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
            start_tls=True,
            timeout=settings.SMTP_TIMEOUT_SECONDS,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        if not settings.RESEND_API_KEY and await _send_email_via_resend_api(
            to_email, subject, html_content, text_content
        ):
            return True
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
    try:
        # Render template
        template = template_env.get_template("otp_email.html")
        html_content = template.render(
            otp=otp, name=name or "User", expiry_minutes=settings.OTP_EXPIRY_MINUTES
        )
    except Exception as e:
        logger.error(f"Failed to render OTP email template for {email}: {str(e)}")
        return False

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
        text_content=text_content,
    )

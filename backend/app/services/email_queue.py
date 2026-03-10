# backend/app/services/email/email_queue.py

"""
Email queue with Redis and retry logic.
Author: Kalidu
Story: CD-120.3
"""

import json
import uuid
from typing import Dict, Optional
from datetime import datetime

from app.core.database import SessionLocal
from app.services.email import send_email, send_otp_email
from app.modules.notifications.models import EmailLog, EmailStatus
from app.core.redis_client import get_redis


class EmailQueue:
    """
    Email queue with Redis backend.

    Story: CD-120.3 - Queue with retry
    """

    def __init__(self):
        """Initialize Redis queue settings."""
        self.queue_key = "email_queue"
        self.processing_key = "email_processing"
        # We will use the existing redis connection pool when needed (async)

    async def enqueue(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        priority: int = 5,
    ) -> str:
        """
        Add email to queue.

        Story: CD-120.3

        Args:
            to_email: Recipient
            subject: Subject line
            html_body: Direct HTML
            text_body: Direct Text
            priority: Priority (1=highest, 10=lowest)

        Returns:
            Email ID
        """
        email_id = str(uuid.uuid4())

        email_data = {
            "id": email_id,
            "to_email": to_email,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
            "priority": priority,
            "retry_count": 0,
            "max_retries": 3,
            "created_at": datetime.utcnow().isoformat(),
        }

        redis_client = await get_redis()
        # Add to queue with priority score
        await redis_client.zadd(self.queue_key, {json.dumps(email_data): priority})

        return email_id

    async def process_queue(self) -> int:
        """
        Process emails from queue.

        Story: CD-120.3, CD-120.4

        Returns:
            Number of emails processed
        """
        processed = 0
        redis_client = await get_redis()

        # Get pending emails (sorted by priority)
        emails = await redis_client.zrange(self.queue_key, 0, 9)  # Process 10 at a time

        if not emails:
            return 0

        db = SessionLocal()

        try:
            for email_json in emails:
                email_data = json.loads(email_json)

                # Create detailed log entry
                email_log = EmailLog(
                    to_email=email_data["to_email"],
                    from_email="noreply@cleardrive.lk",  # configured sender
                    subject=email_data["subject"],
                    html_body=email_data["html_body"],
                    text_body=email_data.get("text_body"),
                    status=EmailStatus.SENDING,
                    retry_count=email_data["retry_count"],
                    max_retries=email_data["max_retries"],
                )
                db.add(email_log)
                db.commit()
                db.refresh(email_log)

                # Send email via actual service
                success = await send_email(
                    to_email=email_data["to_email"],
                    subject=email_data["subject"],
                    html_content=email_data["html_body"],
                    text_content=email_data.get("text_body"),
                )

                if success:
                    # Remove from queue
                    await redis_client.zrem(self.queue_key, email_json)
                    processed += 1

                    email_log.status = EmailStatus.SENT
                    email_log.sent_at = datetime.utcnow()
                else:
                    # Increment retry count
                    email_data["retry_count"] += 1
                    email_log.retry_count = email_data["retry_count"]

                    if email_data["retry_count"] >= email_data["max_retries"]:
                        # Max retries reached, remove from queue
                        await redis_client.zrem(self.queue_key, email_json)
                        email_log.status = EmailStatus.FAILED
                        email_log.failed_at = datetime.utcnow()
                        email_log.error_message = "Max retries reached"
                    else:
                        # Update and re-queue with delay
                        await redis_client.zrem(self.queue_key, email_json)

                        # Increase priority score (lower priority)
                        new_priority = email_data["priority"] + 5

                        await redis_client.zadd(
                            self.queue_key, {json.dumps(email_data): new_priority}
                        )
                        email_log.status = EmailStatus.QUEUED

                db.commit()

        finally:
            db.close()

        return processed


# Global instance
email_queue = EmailQueue()

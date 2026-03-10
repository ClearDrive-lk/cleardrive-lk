# backend/app/services/email_scheduler.py

"""
Email queue processor scheduler.
Author: Kalidu
Story: CD-120.4 - Async email sending
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.email_queue import email_queue


class EmailScheduler:
    """
    Schedule periodic email queue processing.

    Story: CD-120.4
    """

    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    async def process_emails(self):
        """Process email queue."""
        try:
            await email_queue.process_queue()
        except Exception as e:
            print(f"❌ Email processing error: {e}")

    def start(self):
        """Start the email scheduler."""

        if self.is_running:
            print("⚠️  Email scheduler already running")
            return

        # Process queue every 60 seconds
        self.scheduler.add_job(
            func=self.process_emails,
            trigger=IntervalTrigger(seconds=60),
            id="email_queue_processor",
            name="Email Queue Processor",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True

        print(f"\n{'='*70}")
        print(f"✅ EMAIL SCHEDULER STARTED")
        print(f"   Interval: Every 60 seconds")
        print(f"{'='*70}\n")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            print("🛑 Email scheduler stopped")


# Global instance
email_scheduler = EmailScheduler()

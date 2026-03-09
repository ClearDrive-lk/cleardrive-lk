from __future__ import annotations

import logging

from app.core.database import SessionLocal
from app.services.security.file_integrity import file_integrity_service

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    APSCHEDULER_AVAILABLE = True
except Exception:  # pragma: no cover
    BackgroundScheduler = None  # type: ignore[assignment]
    CronTrigger = None  # type: ignore[assignment]
    APSCHEDULER_AVAILABLE = False


class IntegrityScheduler:
    def __init__(self) -> None:
        self.scheduler = (
            BackgroundScheduler(timezone="Asia/Colombo") if APSCHEDULER_AVAILABLE else None
        )
        self.is_running = False

    def run_verification(self) -> dict[str, object]:
        db = SessionLocal()
        try:
            stats = file_integrity_service.verify_all_files(db)
            logger.info("CD-53 integrity verification completed: %s", stats)
            return stats
        finally:
            db.close()

    def start(self) -> None:
        if not APSCHEDULER_AVAILABLE:
            logger.warning("APScheduler not installed. CD-53 integrity scheduler disabled.")
            return
        if self.is_running or self.scheduler is None:
            return
        self.scheduler.add_job(
            func=self.run_verification,
            trigger=CronTrigger(hour=2, minute=0),
            id="daily_integrity_verification",
            name="Daily File Integrity Verification",
            replace_existing=True,
        )
        self.scheduler.start()
        self.is_running = True
        logger.info(
            "CD-53 integrity scheduler started: daily at 02:00 (next=%s)",
            self.scheduler.get_job("daily_integrity_verification").next_run_time,
        )

    def stop(self) -> None:
        if self.scheduler is not None and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.is_running = False

    def run_now(self) -> dict[str, object]:
        return self.run_verification()


integrity_scheduler = IntegrityScheduler()

# backend/app/modules/notifications/worker.py

import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.modules.notifications.queue import email_queue
from backend.app.modules.notifications.service import email_service

logger = logging.getLogger(__name__)


class EmailQueueWorker:
    """Background worker to process email queue"""
    
    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the email queue worker"""
        if self.running:
            logger.warning("Email queue worker is already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._process_queue())
        logger.info("Email queue worker started")
    
    async def stop(self):
        """Stop the email queue worker"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Email queue worker stopped")
    
    async def _process_queue(self):
        """Main queue processing loop"""
        logger.info("Email queue processing loop started")
        
        while self.running:
            try:
                # Get next email from queue (blocking with 1 second timeout)
                email_data = email_queue.dequeue(timeout=1)
                
                if email_data is None:
                    # No emails in queue, wait a bit
                    await asyncio.sleep(0.5)
                    continue
                
                # Process email
                await self._process_email(email_data)
                
            except Exception as e:
                logger.error(f"Error in queue processing loop: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight error loop
    
    async def _process_email(self, email_data: dict):
        """Process a single email from the queue"""
        email_log_id = email_data.get('email_log_id')
        
        try:
            # Create database session
            db: Session = SessionLocal()
            
            try:
                # Process the email
                success = await email_service.process_queue_item(db, email_data)
                
                if success:
                    logger.info(f"Successfully processed email {email_log_id}")
                else:
                    logger.warning(f"Failed to process email {email_log_id}")
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error processing email {email_log_id}: {str(e)}")


# Global worker instance
email_queue_worker = EmailQueueWorker()


# Startup and shutdown event handlers for FastAPI
async def start_email_worker():
    """Start email worker on application startup"""
    await email_queue_worker.start()


async def stop_email_worker():
    """Stop email worker on application shutdown"""
    await email_queue_worker.stop()

# backend/app/modules/notifications/queue.py

import json
import redis
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class EmailQueue:
    """Redis-based email queue with retry logic"""
    
    # Queue names
    QUEUE_PENDING = "email:queue:pending"
    QUEUE_PROCESSING = "email:queue:processing"
    QUEUE_FAILED = "email:queue:failed"
    QUEUE_DEAD_LETTER = "email:queue:dead_letter"
    
    # Tracking
    COUNTER_SENT_TODAY = "email:counter:sent:today"
    RATE_LIMIT_KEY = "email:ratelimit:{user_id}"
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize email queue"""
        if redis_client is None:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
        else:
            self.redis_client = redis_client
        
        logger.info("Email queue initialized")
    
    def enqueue(
        self,
        email_log_id: int,
        recipient_email: str,
        subject: str,
        html_content: str,
        text_content: str = "",
        priority: str = "NORMAL"
    ) -> bool:
        """
        Add email to queue
        
        Args:
            email_log_id: Database ID of email log
            recipient_email: Recipient's email
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text fallback
            priority: Email priority (URGENT, HIGH, NORMAL, LOW)
        
        Returns:
            True if enqueued successfully
        """
        try:
            email_data = {
                "email_log_id": email_log_id,
                "recipient_email": recipient_email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "priority": priority,
                "enqueued_at": datetime.utcnow().isoformat(),
                "attempts": 0,
            }
            
            # Serialize to JSON
            email_json = json.dumps(email_data)
            
            # Add to queue based on priority
            if priority == "URGENT":
                # Use LPUSH for urgent emails (front of queue)
                self.redis_client.lpush(self.QUEUE_PENDING, email_json)
            else:
                # Use RPUSH for normal priority (back of queue)
                self.redis_client.rpush(self.QUEUE_PENDING, email_json)
            
            logger.info(f"Email {email_log_id} enqueued for {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue email {email_log_id}: {str(e)}")
            return False
    
    def dequeue(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get next email from queue (blocking operation)
        
        Args:
            timeout: Seconds to wait for item (0 = don't wait)
        
        Returns:
            Email data dict or None
        """
        try:
            # BLPOP: Blocking pop from left (FIFO)
            result = self.redis_client.blpop(self.QUEUE_PENDING, timeout=timeout)
            
            if result is None:
                return None
            
            queue_name, email_json = result
            email_data = json.loads(email_json)
            
            # Move to processing queue (for crash recovery)
            self.redis_client.rpush(self.QUEUE_PROCESSING, email_json)
            
            logger.info(f"Dequeued email {email_data['email_log_id']}")
            return email_data
            
        except Exception as e:
            logger.error(f"Failed to dequeue email: {str(e)}")
            return None
    
    def mark_sent(self, email_log_id: int) -> bool:
        """Mark email as successfully sent"""
        try:
            # Remove from processing queue
            self._remove_from_processing(email_log_id)
            
            # Increment sent counter
            self.redis_client.incr(self.COUNTER_SENT_TODAY)
            
            # Set counter expiry to end of day
            now = datetime.utcnow()
            end_of_day = now.replace(hour=23, minute=59, second=59)
            ttl = int((end_of_day - now).total_seconds())
            self.redis_client.expire(self.COUNTER_SENT_TODAY, ttl)
            
            logger.info(f"Email {email_log_id} marked as sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark email {email_log_id} as sent: {str(e)}")
            return False
    
    def mark_failed(
        self,
        email_log_id: int,
        email_data: Dict[str, Any],
        error_message: str,
        max_attempts: int = 3
    ) -> bool:
        """
        Mark email as failed and retry if attempts < max_attempts
        
        Args:
            email_log_id: Email log ID
            email_data: Original email data
            error_message: Error message
            max_attempts: Maximum retry attempts
        
        Returns:
            True if handled successfully
        """
        try:
            attempts = email_data.get('attempts', 0) + 1
            email_data['attempts'] = attempts
            email_data['last_error'] = error_message
            email_data['last_attempt_at'] = datetime.utcnow().isoformat()
            
            # Remove from processing
            self._remove_from_processing(email_log_id)
            
            if attempts < max_attempts:
                # Retry: Add back to pending queue with exponential backoff
                # Delay = 2^attempts minutes (1, 2, 4 minutes)
                delay_seconds = 60 * (2 ** (attempts - 1))
                
                email_json = json.dumps(email_data)
                
                # For simplicity, we'll just add it back to pending
                # In production, use Redis sorted sets for delayed retry
                self.redis_client.rpush(self.QUEUE_PENDING, email_json)
                
                logger.warning(
                    f"Email {email_log_id} failed (attempt {attempts}/{max_attempts}). "
                    f"Will retry. Error: {error_message}"
                )
            else:
                # Max attempts reached: Move to dead letter queue
                email_json = json.dumps(email_data)
                self.redis_client.rpush(self.QUEUE_DEAD_LETTER, email_json)
                
                logger.error(
                    f"Email {email_log_id} moved to dead letter queue after {attempts} attempts. "
                    f"Error: {error_message}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle failed email {email_log_id}: {str(e)}")
            return False
    
    def _remove_from_processing(self, email_log_id: int) -> bool:
        """Remove email from processing queue"""
        try:
            # Get all items from processing queue
            processing_items = self.redis_client.lrange(self.QUEUE_PROCESSING, 0, -1)
            
            for item in processing_items:
                email_data = json.loads(item)
                if email_data['email_log_id'] == email_log_id:
                    # Remove this specific item
                    self.redis_client.lrem(self.QUEUE_PROCESSING, 1, item)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove email {email_log_id} from processing: {str(e)}")
            return False
    
    def get_queue_size(self, queue_name: str = None) -> int:
        """Get size of a queue"""
        try:
            if queue_name is None:
                queue_name = self.QUEUE_PENDING
            return self.redis_client.llen(queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue size for {queue_name}: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get email queue statistics"""
        try:
            return {
                "pending": self.get_queue_size(self.QUEUE_PENDING),
                "processing": self.get_queue_size(self.QUEUE_PROCESSING),
                "failed": self.get_queue_size(self.QUEUE_FAILED),
                "dead_letter": self.get_queue_size(self.QUEUE_DEAD_LETTER),
                "sent_today": int(self.redis_client.get(self.COUNTER_SENT_TODAY) or 0),
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {str(e)}")
            return {}
    
    def check_rate_limit(self, user_id: int, max_per_hour: int = 10) -> bool:
        """
        Check if user has exceeded email rate limit
        
        Args:
            user_id: User ID
            max_per_hour: Maximum emails per hour
        
        Returns:
            True if within limit, False if exceeded
        """
        try:
            key = self.RATE_LIMIT_KEY.format(user_id=user_id)
            count = self.redis_client.get(key)
            
            if count is None:
                # First email in this hour
                self.redis_client.setex(key, 3600, 1)  # Expire in 1 hour
                return True
            
            count = int(count)
            if count >= max_per_hour:
                logger.warning(f"Rate limit exceeded for user {user_id}: {count}/{max_per_hour}")
                return False
            
            # Increment counter
            self.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed for user {user_id}: {str(e)}")
            # Fail open (allow email) on error
            return True
    
    def clear_queue(self, queue_name: str) -> bool:
        """Clear a queue (admin only)"""
        try:
            self.redis_client.delete(queue_name)
            logger.warning(f"Queue {queue_name} cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue {queue_name}: {str(e)}")
            return False


# Singleton instance
email_queue = EmailQueue()

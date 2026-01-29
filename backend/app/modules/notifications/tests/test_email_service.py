# backend/app/modules/notifications/tests/test_email_service.py

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.modules.notifications.service import email_service, send_otp_email
from app.modules.notifications.schemas import EmailRequest, EmailTemplate, EmailPriority, EmailResponse
from app.modules.notifications.models import EmailLog, EmailStatus
from app.modules.notifications.templates import template_engine
from app.modules.notifications.queue import EmailQueue


class TestEmailTemplateEngine:
    """Test email template rendering"""
    
    def test_render_otp_template(self):
        """Test OTP template rendering"""
        context = {
            "otp_code": "123456",
            "expires_in_minutes": 5
        }
        
        html = template_engine.render_template(
            template_name="otp",
            context=context,
            recipient_email="test@example.com",
            recipient_name="Test User"
        )
        
        assert "123456" in html
        assert "Test User" in html
        assert "5 minutes" in html or "5" in html
        assert "ClearDrive.lk" in html
    
    def test_render_order_confirmation_template(self):
        """Test order confirmation template rendering"""
        context = {
            "order_id": "CD-ORD-12345",
            "vehicle_make": "Toyota",
            "vehicle_model": "Prius",
            "vehicle_year": "2020",
            "total_amount": "3,500,000",
            "order_date": "2026-01-27",
            "order_status": "PENDING",
            "order_url": "https://cleardrive.lk/orders/12345"
        }
        
        html = template_engine.render_template(
            template_name="order_confirmation",
            context=context,
            recipient_email="test@example.com",
            recipient_name="Test User"
        )
        
        assert "CD-ORD-12345" in html
        assert "Toyota Prius" in html
        assert "2020" in html
    
    def test_invalid_template_name(self):
        """Test that invalid template name raises error"""
        with pytest.raises(ValueError, match="does not exist"):
            template_engine.render_template(
                template_name="nonexistent_template",
                context={},
                recipient_email="test@example.com"
            )
    
    def test_list_available_templates(self):
        """Test listing available templates"""
        templates = template_engine.list_available_templates()
        
        assert isinstance(templates, list)
        assert "otp" in templates
        assert "order_confirmation" in templates
        assert "base" not in templates  # Base template should be excluded


class TestEmailQueue:
    """Test email queue operations"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return MagicMock()
    
    def test_enqueue_email(self, mock_redis):
        """Test adding email to queue"""
        queue = EmailQueue(redis_client=mock_redis)
        
        result = queue.enqueue(
            email_log_id=1,
            recipient_email="test@example.com",
            subject="Test Email",
            html_content="<p>Test</p>",
            text_content="Test",
            priority="NORMAL"
        )
        
        assert result is True
        assert mock_redis.rpush.called or mock_redis.lpush.called
    
    def test_enqueue_urgent_email(self, mock_redis):
        """Test urgent emails go to front of queue"""
        queue = EmailQueue(redis_client=mock_redis)
        
        queue.enqueue(
            email_log_id=1,
            recipient_email="test@example.com",
            subject="Urgent Email",
            html_content="<p>Urgent</p>",
            priority="URGENT"
        )
        
        # Urgent emails use LPUSH (front of queue)
        assert mock_redis.lpush.called
    
    def test_get_queue_size(self, mock_redis):
        """Test getting queue size"""
        mock_redis.llen.return_value = 5
        queue = EmailQueue(redis_client=mock_redis)
        
        size = queue.get_queue_size()
        
        assert size == 5
        assert mock_redis.llen.called
    
    def test_rate_limiting(self, mock_redis):
        """Test rate limiting"""
        mock_redis.get.return_value = "5"  # User has sent 5 emails
        queue = EmailQueue(redis_client=mock_redis)
        
        # Should allow (under limit of 10)
        result = queue.check_rate_limit(user_id=1, max_per_hour=10)
        assert result is True
        
        # Exceed limit
        mock_redis.get.return_value = "10"
        result = queue.check_rate_limit(user_id=1, max_per_hour=10)
        assert result is False
    
    def test_mark_sent(self, mock_redis):
        """Test marking email as sent"""
        queue = EmailQueue(redis_client=mock_redis)
        
        result = queue.mark_sent(email_log_id=1)
        
        assert result is True
        assert mock_redis.incr.called  # Should increment sent counter


class TestEmailService:
    """Test email service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None
        return db
    
    @pytest.mark.asyncio
    async def test_send_email_async_success(self):
        """Test successful async email sending"""
        with patch('backend.app.modules.notifications.service.aiosmtplib.SMTP') as mock_smtp:
            # Mock successful SMTP connection
            mock_smtp.return_value.__aenter__.return_value = mock_smtp.return_value
            
            success, error = await email_service.send_email_async(
                recipient_email="test@example.com",
                recipient_name="Test User",
                subject="Test Email",
                html_content="<p>Test</p>",
                text_content="Test"
            )
            
            assert success is True
            assert error is None
    
    @pytest.mark.asyncio
    async def test_send_email_async_failure(self):
        """Test failed async email sending"""
        with patch('backend.app.modules.notifications.service.aiosmtplib.SMTP') as mock_smtp:
            # Mock SMTP failure
            mock_smtp.return_value.__aenter__.side_effect = Exception("SMTP error")
            
            success, error = await email_service.send_email_async(
                recipient_email="test@example.com",
                recipient_name="Test User",
                subject="Test Email",
                html_content="<p>Test</p>"
            )
            
            assert success is False
            assert error is not None
            assert "error" in error.lower()
    
    @pytest.mark.asyncio
    async def test_send_templated_email_queued(self, mock_db):
        """Test sending templated email (queued)"""
        with patch('backend.app.modules.notifications.service.email_queue') as mock_queue:
            mock_queue.enqueue.return_value = True
            mock_queue.check_rate_limit.return_value = True
            
            email_request = EmailRequest(
                recipient_email="test@example.com",
                recipient_name="Test User",
                subject="Test OTP",
                template=EmailTemplate.OTP,
                template_data={
                    "otp_code": "123456",
                    "expires_in_minutes": 5
                },
                priority=EmailPriority.HIGH
            )
            
            response = await email_service.send_templated_email(
                db=mock_db,
                email_request=email_request,
                user_id=1,
                queue_email=True
            )
            
            assert response.success is True
            assert response.queued is True
            assert response.email_log_id is not None
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, mock_db):
        """Test rate limit blocking"""
        with patch('backend.app.modules.notifications.service.email_queue') as mock_queue:
            mock_queue.check_rate_limit.return_value = False  # Rate limit exceeded
            
            email_request = EmailRequest(
                recipient_email="test@example.com",
                subject="Test",
                template=EmailTemplate.OTP,
                template_data={"otp_code": "123456"}
            )
            
            response = await email_service.send_templated_email(
                db=mock_db,
                email_request=email_request,
                user_id=1,
                queue_email=True
            )
            
            assert response.success is False
            assert "rate limit" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_otp_email_helper(self, mock_db):
        """Test OTP email helper function"""
        with patch('backend.app.modules.notifications.service.email_service') as mock_service:
            mock_service.send_templated_email = asyncio.coroutine(
                lambda *args, **kwargs: EmailResponse(
                    success=True,
                    message="Email sent",
                    queued=False
                )
            )
            
            response = await send_otp_email(
                db=mock_db,
                recipient_email="test@example.com",
                recipient_name="Test User",
                otp_code="123456",
                expires_in_minutes=5,
                user_id=1
            )
            
            assert response.success is True


class TestEmailLog:
    """Test EmailLog model"""
    
    def test_can_retry_property(self):
        """Test can_retry property"""
        # Can retry: attempts < max_attempts and status is FAILED
        email_log = EmailLog(
            recipient_email="test@example.com",
            subject="Test",
            template_name="otp",
            status=EmailStatus.FAILED,
            attempts=1,
            max_attempts=3
        )
        
        assert email_log.can_retry is True
        
        # Cannot retry: max attempts reached
        email_log.attempts = 3
        assert email_log.can_retry is False
        
        # Cannot retry: already sent
        email_log.status = EmailStatus.SENT
        email_log.attempts = 1
        assert email_log.can_retry is False
    
    def test_is_final_state(self):
        """Test is_final_state property"""
        email_log = EmailLog(
            recipient_email="test@example.com",
            subject="Test",
            template_name="otp",
            status=EmailStatus.SENT,
            attempts=1,
            max_attempts=3
        )
        
        assert email_log.is_final_state is True
        
        # Pending is not final
        email_log.status = EmailStatus.PENDING
        assert email_log.is_final_state is False
        
        # Failed with retries available is not final
        email_log.status = EmailStatus.FAILED
        email_log.attempts = 1
        assert email_log.is_final_state is False
        
        # Failed with no retries is final
        email_log.attempts = 3
        assert email_log.is_final_state is True


# Run tests with: pytest backend/app/modules/notifications/tests/test_email_service.py -v

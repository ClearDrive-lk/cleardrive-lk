import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.notification_service import notification_service


@pytest.fixture
def mock_enqueue():
    with patch(
        "app.services.notification_service.email_queue.enqueue", new_callable=AsyncMock
    ) as mock:
        mock.return_value = "mock_email_id"
        yield mock


@pytest.fixture
def mock_base_otp():
    with patch(
        "app.services.notification_service.base_send_otp_email", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        yield mock


@pytest.mark.asyncio
async def test_send_otp_email(mock_base_otp):
    result = await notification_service.send_otp_email("test@example.com", "123456", "John")
    assert result is True
    mock_base_otp.assert_called_once_with("test@example.com", "123456", "John")


@pytest.mark.asyncio
async def test_send_order_confirmation(mock_enqueue):
    email_id = await notification_service.send_order_confirmation(
        email="test@example.com",
        user_name="John",
        order_id="123",
        vehicle_name="Toyota Prius 2020",
        chassis_no="ZVW50-XXXXXXX",
        total_price="LKR 8,000,000",
    )
    assert email_id == "mock_email_id"
    mock_enqueue.assert_called_once()
    kwargs = mock_enqueue.call_args.kwargs
    assert kwargs["to_email"] == "test@example.com"
    assert "Order Confirmation #123" in kwargs["subject"]
    assert "Toyota Prius 2020" in kwargs["html_body"]
    assert kwargs["priority"] == 2


@pytest.mark.asyncio
async def test_send_payment_confirmation(mock_enqueue):
    email_id = await notification_service.send_payment_confirmation(
        email="test@example.com",
        user_name="John",
        order_id="123",
        amount="LKR 8,000,000",
        receipt_id="REC-001",
        payment_date="2026-03-11",
        payment_method="Credit Card",
    )
    assert email_id == "mock_email_id"
    mock_enqueue.assert_called_once()
    kwargs = mock_enqueue.call_args.kwargs
    assert kwargs["to_email"] == "test@example.com"
    assert "Payment Received for Order #123" in kwargs["subject"]
    assert "LKR 8,000" in kwargs["html_body"]
    assert kwargs["priority"] == 3


@pytest.mark.asyncio
async def test_send_kyc_approved(mock_enqueue):
    email_id = await notification_service.send_kyc_approved("test@example.com", "John")
    assert email_id == "mock_email_id"
    mock_enqueue.assert_called_once()
    kwargs = mock_enqueue.call_args.kwargs
    assert kwargs["to_email"] == "test@example.com"
    assert "KYC Verification Approved" in kwargs["subject"]
    assert "Approved" in kwargs["html_body"]


@pytest.mark.asyncio
async def test_send_kyc_rejected(mock_enqueue):
    email_id = await notification_service.send_kyc_rejected(
        "test@example.com", "John", "Blurry image"
    )
    assert email_id == "mock_email_id"
    mock_enqueue.assert_called_once()
    kwargs = mock_enqueue.call_args.kwargs
    assert "KYC Verification Update" in kwargs["subject"]
    assert "Blurry image" in kwargs["html_body"]


@pytest.mark.asyncio
async def test_send_shipment_notification(mock_enqueue):
    email_id = await notification_service.send_shipment_notification(
        email="test@example.com",
        user_name="John",
        order_id="123",
        vessel_name="Oceania",
        tracking_number="TRK-999",
        estimated_arrival="2026-04-10",
    )
    assert email_id == "mock_email_id"
    mock_enqueue.assert_called_once()
    kwargs = mock_enqueue.call_args.kwargs
    assert kwargs["to_email"] == "test@example.com"
    assert "Shipment Update for Order #123" in kwargs["subject"]
    assert "Oceania" in kwargs["html_body"]
    assert "TRK-999" in kwargs["html_body"]


@pytest.mark.asyncio
async def test_send_status_change(mock_enqueue):
    email_id = await notification_service.send_status_change(
        email="test@example.com",
        user_name="John",
        order_id="123",
        new_status="Delivered",
        status_message="Thank you for your purchase!",
    )
    assert email_id == "mock_email_id"
    mock_enqueue.assert_called_once()
    kwargs = mock_enqueue.call_args.kwargs
    assert "Status Update for Order #123" in kwargs["subject"]
    assert "Delivered" in kwargs["html_body"]
    assert "Thank you for your purchase!" in kwargs["html_body"]

import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.services.notification_service import notification_service
from app.services.email_queue import email_queue
from app.core.database import SessionLocal


async def test_emails():
    print("Testing NotificationService...")
    test_email = os.environ.get("TEST_EMAIL", "test@cleardrive.lk")
    # 1. Order Confirmation
    print(f"Sending Order Confirmation to {test_email}...")
    await notification_service.send_order_confirmation(
        email=test_email,
        user_name="John Doe",
        order_id="ORD-12345",
        vehicle_name="Toyota Prius 2020",
        chassis_no="ZVW50-1234567",
        stock_no="STK-0001",
        address="No.1, Galle Road, Colombo 03",
        tracking_number="TRK-12345",
        total_price="LKR 8,500,000.00"
    )

    # 2. Payment Confirmation
    print(f"Sending Payment Confirmation to {test_email}...")
    await notification_service.send_payment_confirmation(
        email=test_email,
        user_name="John Doe",
        order_id="ORD-12345",
        amount="LKR 8,500,000.00",
        receipt_id="REC-98765",
        payment_date="2026-03-11 10:30:00",
        payment_method="Credit Card"
    )
    # 3. KYC Approved
    print(f"Sending KYC Approved to {test_email}...")
    await notification_service.send_kyc_approved(
        email=test_email,
        user_name="John Doe"
    )
    # 4. KYC Rejected
    print(f"Sending KYC Rejected to {test_email}...")
    await notification_service.send_kyc_rejected(
        email=test_email,
        user_name="John Doe",
        rejection_reason="The uploaded document is blurry and unreadable."
    )
    # 5. Shipment Notification
    print(f"Sending Shipment Notification to {test_email}...")
    await notification_service.send_shipment_notification(
        email=test_email,
        user_name="John Doe",
        order_id="ORD-12345",
        vessel_name="Ocean Navigator",
        tracking_number="TRK-11223344",
        estimated_arrival="2026-04-15"
    )
    # 6. Status Change
    print(f"Sending Status Change to {test_email}...")
    await notification_service.send_status_change(
        email=test_email,
        user_name="John Doe",
        order_id="ORD-12345",
        new_status="Customs Clearance",
        status_message="Your vehicle has arrived at the port and is undergoing customs clearance."
    )
    print("Enqueued all 6 emails. Now running queue processor...")
    # NOTE: In test environments, queue execution depends on redis connection.
    # To process them here:
    count = await email_queue.process_queue()
    print(f"Processed {count} emails from queue.")
    # Also verify that logs are created
    db = SessionLocal()
    try:
        from app.modules.notifications.models import EmailLog
        count_db = db.query(EmailLog).filter(EmailLog.to_email == test_email).count()
        print(f"Found {count_db} email logs in database for {test_email}.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_emails())

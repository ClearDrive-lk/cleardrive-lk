"""
Email testing endpoints.
Author: Parindra Gallage
Story: CD-550
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.modules.auth.models import User
from app.services.email import send_email
from app.services.email_queue import email_queue

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/test-email")
async def send_test_email(
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Send test email (Admin only).
    
    **Story**: CD-120 - Email testing
    """
    
    from app.services.email import template_env

    template = template_env.get_template("test_email.html")
    html_content = template.render(name=current_admin.name or 'Admin', frontend_url='http://localhost:3000')

    # Send test email
    success = await send_email(
        to_email=current_admin.email,
        subject="ClearDrive Email Test",
        html_content=html_content
    )
    
    if success:
        return {
            "message": "Test email sent successfully",
            "to_email": current_admin.email
        }
    else:
        return {
            "message": "Test email failed to send",
            "to_email": current_admin.email
        }


@router.post("/queue-test-email")
async def queue_test_email(
    current_admin: User = Depends(get_current_admin)
):
    """
    Queue test email (Admin only).
    
    **Story**: CD-120.3 - Email queue testing
    """
    from app.services.email import template_env

    template = template_env.get_template("test_email.html")
    html_content = template.render(name=current_admin.name or 'Admin', frontend_url='http://localhost:3000')

    email_id = await email_queue.enqueue(
        to_email=current_admin.email,
        subject="ClearDrive Queued Email Test",
        html_body=html_content,
        priority=1  # High priority
    )
    
    return {
        "message": "Email queued successfully",
        "email_id": email_id,
        "note": "Email will be sent within 60 seconds"
    }

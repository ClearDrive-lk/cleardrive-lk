"""
GDPR compliance endpoints including policy pages.
Author: Kalidu
Story: CD-460 - Privacy & Cookie Policies
Story: CD-102 - GDPR Data Export
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import markdown  # type: ignore[import-untyped]
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user
from app.modules.auth.models import User
from app.modules.gdpr.models import GDPRDeletion, GDPRExport
from app.services.gdpr.data_deletion_service import data_deletion_service
from app.services.gdpr.data_export_service import data_export_service
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


# ===================================================================
# ENDPOINT: PRIVACY POLICY (CD-462)
# ===================================================================


@router.get("/privacy-policy", response_class=HTMLResponse)
async def get_privacy_policy():
    """
    Serve privacy policy page.

    **Story**: CD-100 - Privacy & Cookie Policies

    **Returns:**
    - HTML version of privacy policy
    - Styled for readability
    - Mobile-responsive

    **Access:** Public (no authentication required)
    """

    # Get policy file path
    policy_path = Path(__file__).parent.parent.parent / "static" / "privacy-policy.md"

    if not policy_path.exists():
        raise HTTPException(
            status_code=404, detail="Privacy policy not found. Please contact support."
        )

    # Read markdown content
    with open(policy_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    # Wrap in styled HTML template
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Privacy Policy - ClearDrive.lk</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f5f5;
                padding: 20px;
            }}

            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}

            h1 {{
                color: #1a1a1a;
                font-size: 2.5em;
                margin-bottom: 10px;
                border-bottom: 3px solid #007bff;
                padding-bottom: 10px;
            }}

            h2 {{
                color: #2c3e50;
                font-size: 1.8em;
                margin-top: 40px;
                margin-bottom: 15px;
                border-left: 4px solid #007bff;
                padding-left: 15px;
            }}

            h3 {{
                color: #34495e;
                font-size: 1.3em;
                margin-top: 25px;
                margin-bottom: 10px;
            }}

            p {{
                margin-bottom: 15px;
                text-align: justify;
            }}

            ul, ol {{
                margin-left: 30px;
                margin-bottom: 15px;
            }}

            li {{
                margin-bottom: 8px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                overflow-x: auto;
                display: block;
            }}

            table thead {{
                background: #007bff;
                color: white;
            }}

            table th, table td {{
                padding: 12px;
                text-align: left;
                border: 1px solid #ddd;
            }}

            table tbody tr:nth-child(even) {{
                background: #f8f9fa;
            }}

            strong {{
                color: #007bff;
                font-weight: 600;
            }}

            em {{
                font-style: italic;
                color: #666;
            }}

            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}

            hr {{
                border: none;
                border-top: 2px solid #e0e0e0;
                margin: 30px 0;
            }}

            .highlight {{
                background: #fff3cd;
                padding: 15px;
                border-left: 4px solid #ffc107;
                margin: 20px 0;
                border-radius: 4px;
            }}

            .contact-box {{
                background: #e7f3ff;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border: 2px solid #007bff;
            }}

            a {{
                color: #007bff;
                text-decoration: none;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}

                h1 {{
                    font-size: 2em;
                }}

                h2 {{
                    font-size: 1.5em;
                }}

                table {{
                    font-size: 0.9em;
                }}
            }}

            .back-link {{
                display: inline-block;
                margin-bottom: 20px;
                padding: 10px 20px;
                background: #007bff;
                color: white !important;
                border-radius: 5px;
                text-decoration: none;
            }}

            .back-link:hover {{
                background: #0056b3;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to ClearDrive.lk</a>
            {html_content}
            <hr>
            <p style="text-align: center; color: #666; margin-top: 40px;">
                <strong>ClearDrive.lk</strong> - Transparent. Secure. Compliant.<br>
                Questions? Contact us at <a href="mailto:privacy@cleardrive.lk">privacy@cleardrive.lk</a>
            </p>
        </div>
    </body>
    </html>
    """

    return full_html


# ===================================================================
# ENDPOINT: COOKIE POLICY (CD-463)
# ===================================================================


@router.get("/cookie-policy", response_class=HTMLResponse)
async def get_cookie_policy():
    """
    Serve cookie policy page.

    **Story**: CD-100 - Privacy & Cookie Policies

    **Returns:**
    - HTML version of cookie policy
    - Styled for readability
    - Mobile-responsive

    **Access:** Public (no authentication required)
    """

    # Get policy file path
    policy_path = Path(__file__).parent.parent.parent / "static" / "cookie-policy.md"

    if not policy_path.exists():
        raise HTTPException(
            status_code=404, detail="Cookie policy not found. Please contact support."
        )

    # Read markdown content
    with open(policy_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    # Wrap in styled HTML template (same style as privacy policy)
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cookie Policy - ClearDrive.lk</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f5f5;
                padding: 20px;
            }}

            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}

            h1 {{
                color: #1a1a1a;
                font-size: 2.5em;
                margin-bottom: 10px;
                border-bottom: 3px solid #ff9800;
                padding-bottom: 10px;
            }}

            h2 {{
                color: #2c3e50;
                font-size: 1.8em;
                margin-top: 40px;
                margin-bottom: 15px;
                border-left: 4px solid #ff9800;
                padding-left: 15px;
            }}

            h3 {{
                color: #34495e;
                font-size: 1.3em;
                margin-top: 25px;
                margin-bottom: 10px;
            }}

            p {{
                margin-bottom: 15px;
                text-align: justify;
            }}

            ul, ol {{
                margin-left: 30px;
                margin-bottom: 15px;
            }}

            li {{
                margin-bottom: 8px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                overflow-x: auto;
                display: block;
            }}

            table thead {{
                background: #ff9800;
                color: white;
            }}

            table th, table td {{
                padding: 12px;
                text-align: left;
                border: 1px solid #ddd;
            }}

            table tbody tr:nth-child(even) {{
                background: #f8f9fa;
            }}

            strong {{
                color: #ff9800;
                font-weight: 600;
            }}

            a {{
                color: #ff9800;
                text-decoration: none;
            }}

            a:hover {{
                text-decoration: underline;
            }}

            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}

                h1 {{
                    font-size: 2em;
                }}

                h2 {{
                    font-size: 1.5em;
                }}
            }}

            .back-link {{
                display: inline-block;
                margin-bottom: 20px;
                padding: 10px 20px;
                background: #ff9800;
                color: white !important;
                border-radius: 5px;
                text-decoration: none;
            }}

            .back-link:hover {{
                background: #f57c00;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to ClearDrive.lk</a>
            {html_content}
            <hr>
            <p style="text-align: center; color: #666; margin-top: 40px;">
                <strong>ClearDrive.lk</strong> - Transparent. Secure. Compliant.<br>
                Questions? Contact us at <a href="mailto:privacy@cleardrive.lk">privacy@cleardrive.lk</a>
            </p>
        </div>
    </body>
    </html>
    """

    return full_html


# ===================================================================
# ENDPOINT: GDPR DATA EXPORT (CD-102)
# ===================================================================


@router.get("/export")
async def export_user_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    logger.info(
        "GDPR export request user=%s ip=%s",
        current_user.id,
        request.client.host if request.client else "unknown",
    )

    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    recent_exports = (
        db.query(GDPRExport)
        .filter(
            GDPRExport.user_id == current_user.id,
            GDPRExport.requested_at >= twenty_four_hours_ago,
        )
        .count()
    )

    if recent_exports >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum 3 data exports per day. Please try again later.",
        )

    export_record = GDPRExport(
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)

    try:
        user_data = data_export_service.collect_user_data(current_user, db)
        json_export = data_export_service.generate_json_export(user_data)

        filename = (
            "cleardrive_data_export_"
            f"{current_user.id}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        )

        export_record.export_file_path = filename
        export_record.file_size_bytes = len(json_export.encode("utf-8"))
        export_record.completed_at = datetime.utcnow()
        export_record.downloaded_at = datetime.utcnow()
        db.commit()

        return Response(
            content=json_export,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/json; charset=utf-8",
            },
        )
    except Exception:
        logger.exception("GDPR export failed for user=%s", current_user.id)
        export_record.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data export failed. Please contact support.",
        )


@router.get("/export/history")
async def get_export_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's data export history.

    **Story**: CD-102.6
    """

    exports = (
        db.query(GDPRExport)
        .filter(GDPRExport.user_id == current_user.id)
        .order_by(GDPRExport.requested_at.desc())
        .limit(10)
        .all()
    )

    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    recent_count = (
        db.query(GDPRExport)
        .filter(
            GDPRExport.user_id == current_user.id,
            GDPRExport.requested_at >= twenty_four_hours_ago,
        )
        .count()
    )

    return {
        "daily_limit": 3,
        "used_today": recent_count,
        "remaining_today": max(0, 3 - recent_count),
        "export_history": [
            {
                "id": str(export.id),
                "requested_at": export.requested_at.isoformat(),
                "completed_at": export.completed_at.isoformat() if export.completed_at else None,
                "file_size_bytes": export.file_size_bytes,
            }
            for export in exports
        ],
    }


@router.get("/deletion-check")
async def check_deletion_blockers(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if account deletion can proceed for the current user."""
    blocker = data_deletion_service.check_deletion_blockers(current_user, db)
    if blocker.blocked:
        return {"can_delete": False, "blocked": True, "reason": blocker.reason}
    return {
        "can_delete": True,
        "blocked": False,
        "message": "Your account can be deleted. All checks passed.",
    }


@router.get("/deletion-status")
async def get_deletion_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return latest GDPR deletion status for the current user."""
    deletion = (
        db.query(GDPRDeletion)
        .filter(GDPRDeletion.user_id == current_user.id)
        .order_by(GDPRDeletion.requested_at.desc())
        .first()
    )

    if not deletion:
        return {"has_deletion_request": False, "can_delete": True}

    return {
        "has_deletion_request": True,
        "status": deletion.status.value,
        "requested_at": deletion.requested_at.isoformat(),
        "processed_at": deletion.processed_at.isoformat() if deletion.processed_at else None,
        "rejection_reason": deletion.rejection_reason,
    }


@router.delete("/delete")
async def delete_user_data(
    request: Request,
    confirmation: str = Query(..., description="Type 'DELETE MY ACCOUNT' to confirm"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """GDPR Article 17 account deletion implemented as anonymization plus revocation."""
    if confirmation != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation. Type exactly: DELETE MY ACCOUNT",
        )

    success, message, deletion_record = await data_deletion_service.process_deletion(
        user=current_user,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        db=db,
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {
        "message": message,
        "deletion_id": str(deletion_record.id),
        "processed_at": (
            deletion_record.processed_at.isoformat() if deletion_record.processed_at else None
        ),
        "details": {
            "data_anonymized": deletion_record.data_anonymized,
            "kyc_deleted": deletion_record.kyc_deleted,
            "sessions_revoked": deletion_record.sessions_revoked,
        },
        "note": "This action is permanent and cannot be undone.",
    }

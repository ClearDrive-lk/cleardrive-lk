"""
GDPR compliance endpoints including policy pages.
Author: Kalidu
Story: CD-460 - Privacy & Cookie Policies
"""

from pathlib import Path

import markdown
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

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

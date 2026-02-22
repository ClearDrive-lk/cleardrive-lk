# backend/app/middleware/security_headers.py

"""
Security headers middleware.
Implements comprehensive security headers for all responses.
"""

import secrets
from typing import Callable, cast

from app.core.config import settings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Headers added:
    - Content-Security-Policy (CSP) with nonce
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security (HSTS)
    - Referrer-Policy
    - Permissions-Policy
    - X-XSS-Protection
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate nonce for CSP
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        # Process request
        response = await call_next(request)

        # Skip strict CSP for API docs (Swagger/ReDoc load from CDNs and use inline assets)
        docs_paths = ("/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json")
        if (
            request.url.path.rstrip("/") in docs_paths
            or request.url.path.startswith("/api/v1/docs")
            or request.url.path.startswith("/api/v1/redoc")
        ):
            # Only safe headers for docs; no CSP so Swagger UI can load
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return cast(Response, response)

        # Add security headers

        # 1. Content Security Policy (CSP) with nonce
        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' https://accounts.google.com "
            "https://accounts.gstatic.com https://www.googletagmanager.com "
            "https://vercel.live",
            f"script-src-elem 'self' 'nonce-{nonce}' https://accounts.google.com "
            "https://accounts.gstatic.com https://www.googletagmanager.com "
            "https://vercel.live",
            f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com "
            "https://accounts.google.com",
            f"style-src-elem 'self' 'nonce-{nonce}' https://fonts.googleapis.com "
            "https://accounts.google.com",
            "connect-src 'self' https://api.anthropic.com https://*.supabase.co",
            "img-src 'self' data: blob: https://*.supabase.co https://www.google.com",
            "font-src 'self' https://fonts.gstatic.com",
            "frame-src 'self' https://accounts.google.com https://sandbox.payhere.lk",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests",
        ]

        # Add report-uri in production
        if settings.ENVIRONMENT == "production":
            csp_directives.append("report-uri /api/v1/security/csp-report")

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # 2. X-Frame-Options (Prevent clickjacking)
        response.headers["X-Frame-Options"] = "DENY"

        # 3. X-Content-Type-Options (Prevent MIME sniffing)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 4. Strict-Transport-Security (HSTS)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 5. Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 6. Permissions-Policy (formerly Feature-Policy)
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=(self)",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=(self)",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # 7. X-XSS-Protection (Legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 8. X-Permitted-Cross-Domain-Policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. X-Download-Options (IE specific)
        response.headers["X-Download-Options"] = "noopen"

        # 10. Cache-Control for sensitive endpoints
        if any(path in request.url.path for path in ["/auth/", "/admin/", "/kyc/"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return cast(Response, response)

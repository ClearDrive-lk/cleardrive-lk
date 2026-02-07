SECURITY_HEADERS.md
markdown# Security Headers & CSP Policy

## Overview
The backend applies security headers for all non-docs routes via `SecurityHeadersMiddleware`
(`backend/app/middleware/security_headers.py`). This includes a nonce-based CSP.

Docs endpoints (`/api/v1/docs`, `/api/v1/redoc`, `/api/v1/openapi.json`) intentionally skip CSP
because Swagger/ReDoc use inline assets and external CDNs.

## CSP Policy (Backend)
The CSP is emitted as a header and includes a per-request nonce:

- `default-src 'self'`
- `script-src 'self' 'nonce-{nonce}' https://accounts.google.com https://www.googletagmanager.com`
- `style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com`
- `connect-src 'self' https://api.anthropic.com https://*.supabase.co`
- `img-src 'self' data: blob: https://*.supabase.co https://www.google.com`
- `font-src 'self' https://fonts.gstatic.com`
- `frame-src 'self' https://accounts.google.com https://sandbox.payhere.lk`
- `object-src 'none'`
- `base-uri 'self'`
- `form-action 'self'`
- `frame-ancestors 'none'`
- `upgrade-insecure-requests`
- `report-uri /api/v1/security/csp-report` (production only)

## Nonce Usage
The nonce is generated per request in the middleware and attached to the CSP header.
If any server-rendered HTML includes inline scripts/styles, they must include a matching
`nonce` attribute.

Note: The backend currently does not serve HTML pages (other than Swagger/ReDoc),
so there are no runtime HTML inline scripts/styles to annotate.

## Email Templates
Email HTML is not subject to CSP headers, but inline `<style>` tags in email templates
use a nonce attribute for consistency. See `backend/app/templates/email/otp_email.html`.

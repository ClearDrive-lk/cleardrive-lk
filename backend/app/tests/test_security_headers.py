# backend/app/tests/test_security_headers.py
"""
Tests for security headers middleware (CSP nonce, docs exclusions).
"""


def test_csp_header_includes_nonce_and_no_unsafe_inline(client):
    response = client.get("/")
    assert response.status_code == 200

    csp = response.headers.get("Content-Security-Policy")
    assert csp, "CSP header missing"
    assert "'nonce-" in csp, "CSP nonce missing"
    assert "unsafe-inline" not in csp


def test_docs_skip_csp_header(client):
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers

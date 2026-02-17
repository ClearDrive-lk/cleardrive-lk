# backend/app/tests/test_auth.py
"""
Authentication/JWT tests.
"""
<<<<<<< HEAD

=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.core.config import settings
from app.core.redis_client import delete_otp, store_otp
from app.core.security import create_access_token, create_refresh_token, hash_token
from app.modules.auth.models import Role
from app.modules.auth.models import Session as UserSession
from app.modules.auth.models import User
from jose import jwt


def _exp_delta_seconds(token: str) -> float:
    claims = jwt.get_unverified_claims(token)
    exp = datetime.utcfromtimestamp(claims["exp"])
    return (exp - datetime.utcnow()).total_seconds()


def _assert_expiry_close(
    actual_seconds: float, expected_seconds: float, tolerance: int = 5
) -> None:
    assert abs(actual_seconds - expected_seconds) <= tolerance


def test_access_token_expiry_minutes():
    token = create_access_token(data={"sub": "user-id", "email": "a@b.com", "role": "CUSTOMER"})
    delta = _exp_delta_seconds(token)
    expected = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    _assert_expiry_close(delta, expected)


def test_refresh_token_expiry_days():
    token = create_refresh_token(data={"sub": "user-id"})
    delta = _exp_delta_seconds(token)
    expected = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    _assert_expiry_close(delta, expected)


@pytest.mark.asyncio
async def test_verify_otp_creates_session_and_tokens(async_client, db, mocker):
    mocker.patch(
        "app.modules.auth.routes.check_otp_rate_limit",
        return_value=True,
        new_callable=AsyncMock,
    )

    email = "auth_flow@example.com"
    user = User(email=email, name="Auth Flow", role=Role.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)

    otp = "123456"
    await store_otp(email, otp)

    try:
        response = await async_client.post(
            "/api/v1/auth/verify-otp", json={"email": email, "otp": otp}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        session = (
            db.query(UserSession)
            .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
            .first()
        )
        assert session is not None
        assert session.refresh_token_hash == hash_token(data["refresh_token"])

        # Session expiry should be close to configured refresh token expiry
        expected = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        delta = session.expires_at - datetime.utcnow()
        assert abs(delta - expected) < timedelta(minutes=5)
    finally:
        await delete_otp(email)


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_detection(async_client, db, mocker):
    mocker.patch(
        "app.modules.auth.routes.check_otp_rate_limit",
        return_value=True,
        new_callable=AsyncMock,
    )

    email = "rotation@example.com"
    user = User(email=email, name="Rotation User", role=Role.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)

    otp = "123456"
    await store_otp(email, otp)

    try:
        verify_response = await async_client.post(
            "/api/v1/auth/verify-otp", json={"email": email, "otp": otp}
        )
        assert verify_response.status_code == 200
        tokens = verify_response.json()
        old_refresh = tokens["refresh_token"]

        refresh_response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_refresh = new_tokens["refresh_token"]
        assert new_refresh != old_refresh

        session = (
            db.query(UserSession)
            .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
            .first()
        )
        assert session is not None
        assert session.refresh_token_hash == hash_token(new_refresh)

        # Reuse old refresh token should revoke all sessions
        reuse_response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert reuse_response.status_code == 403
        assert "reuse" in reuse_response.json().get("detail", "").lower()

        sessions = db.query(UserSession).filter(UserSession.user_id == user.id).all()
        assert sessions, "Expected at least one session to exist"
        assert all(not s.is_active for s in sessions)
    finally:
        await delete_otp(email)

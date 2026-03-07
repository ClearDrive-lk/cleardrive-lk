"""
Test JWT token management.
"""

from datetime import UTC, datetime, timedelta

import pytest
from app.core.redis import (
    blacklist_token,
    delete_refresh_token,
    get_refresh_token,
    is_token_blacklisted,
    store_refresh_token,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_token,
)
from app.modules.auth.models import Session as UserSession
from app.modules.auth.models import User


class TestTokenGeneration:
    """Test token generation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user-123", "email": "test@example.com", "role": "CUSTOMER"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 50

    def test_access_token_payload(self):
        """Test access token contains correct payload."""
        data = {"sub": "user-123", "email": "test@example.com", "role": "CUSTOMER"}
        token = create_access_token(data)

        payload = decode_access_token(token)

        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "CUSTOMER"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user-123"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 50

    def test_refresh_token_payload(self):
        """Test refresh token contains correct payload."""
        data = {"sub": "user-123"}
        token = create_refresh_token(data)

        payload = decode_refresh_token(token)

        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        assert "jti" in payload


class TestTokenValidation:
    """Test token validation."""

    def test_decode_valid_access_token(self):
        """Test decoding valid access token."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"

    def test_decode_expired_access_token(self):
        """Test decoding expired access token."""
        data = {"sub": "user-123"}

        # Create token with -1 minute expiry (expired)
        token = create_access_token(data, expires_delta=timedelta(minutes=-1))

        assert decode_access_token(token) is None

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        assert decode_access_token("invalid.token.here") is None

    def test_decode_wrong_token_type(self):
        """Test decoding refresh token as access token."""
        token = create_refresh_token({"sub": "user-123"})

        assert decode_access_token(token) is None


@pytest.mark.asyncio
class TestTokenBlacklist:
    """Test token blacklisting."""

    async def test_blacklist_token(self):
        """Test blacklisting a token."""
        token_jti = "test-jti-123"

        await blacklist_token(token_jti, 300)

        is_blacklisted = await is_token_blacklisted(token_jti)
        assert is_blacklisted is True

    async def test_non_blacklisted_token(self):
        """Test checking non-blacklisted token."""
        is_blacklisted = await is_token_blacklisted("non-existent-jti")
        assert is_blacklisted is False


@pytest.mark.asyncio
class TestRefreshTokenStorage:
    """Test refresh token storage."""

    async def test_store_and_get_refresh_token(self):
        """Test storing and retrieving refresh token."""
        token_jti = "test-jti-456"
        user_id = "user-123"
        device_info = {"ip": "127.0.0.1", "user_agent": "test"}

        await store_refresh_token(token_jti, user_id, device_info)

        data = await get_refresh_token(token_jti)

        assert data is not None
        assert data["user_id"] == user_id
        assert data["device_info"]["ip"] == "127.0.0.1"

    async def test_delete_refresh_token(self):
        """Test deleting refresh token."""
        token_jti = "test-jti-789"

        await store_refresh_token(token_jti, "user-123", {})
        await delete_refresh_token(token_jti)

        data = await get_refresh_token(token_jti)
        assert data is None


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_protected_route_with_valid_token(self, client, db):
        """Test accessing protected route with valid token."""
        # Create user
        user = User(email="test@example.com", name="Test User")
        db.add(user)
        db.commit()

        # Create token
        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})

        # Access protected route
        response = client.get(
            "/api/v1/test/protected", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json()["user"]["email"] == "test@example.com"

    async def test_protected_route_without_token(self, client):
        """Test accessing protected route without token."""
        response = client.get("/api/v1/test/protected")

        assert response.status_code == 401

    async def test_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token."""
        response = client.get(
            "/api/v1/test/protected",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    async def test_token_refresh(self, client, db):
        """Test token refresh endpoint."""
        # Create user
        user = User(email="test@example.com", name="Test User")
        db.add(user)
        db.commit()

        # Create refresh token
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Store in Redis
        payload = decode_refresh_token(refresh_token)
        await store_refresh_token(payload.get("jti"), str(user.id), {"ip": "127.0.0.1"})

        # Create DB session (required for refresh)
        db_session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            is_active=True,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(db_session)
        db.commit()

        # Refresh token
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_logout(self, client, db):
        """Test logout endpoint."""
        # Create user and token
        user = User(email="test@example.com", name="Test User")
        db.add(user)
        db.commit()

        token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})

        # Logout
        response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]

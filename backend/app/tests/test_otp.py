# backend/app/tests/test_otp.py
"""
Test OTP generation, storage, and verification.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.core.otp import generate_otp, is_otp_expired, verify_otp_constant_time
from app.core.redis_client import delete_otp, get_otp, increment_otp_attempts, store_otp
from app.modules.auth.models import Role, User


class TestOTPGeneration:
    """Test OTP generation."""

    def test_generate_otp_length(self):
        """Test OTP has correct length."""
        otp = generate_otp(6)
        assert len(otp) == 6

    def test_generate_otp_digits_only(self):
        """Test OTP contains only digits."""
        otp = generate_otp()
        assert otp.isdigit()

    def test_generate_otp_uniqueness(self):
        """Test OTPs are unique (probabilistic)."""
        otps = [generate_otp() for _ in range(100)]
        assert len(set(otps)) > 90  # At least 90% unique


class TestOTPVerification:
    """Test OTP verification."""

    def test_verify_otp_valid(self):
        """Test valid OTP verification."""
        otp = "123456"
        assert verify_otp_constant_time(otp, otp) is True

    def test_verify_otp_invalid(self):
        """Test invalid OTP verification."""
        assert verify_otp_constant_time("123456", "654321") is False

    def test_verify_otp_constant_time(self):
        """Test constant-time property (basic check)."""
        import time

        # Run multiple iterations to get average
        iterations = 100

        # Measure time for matching OTPs
        total_match = 0
        for _ in range(iterations):
            start = time.perf_counter()
            verify_otp_constant_time("123456", "123456")
            total_match += time.perf_counter() - start
        avg_match = total_match / iterations

        # Measure time for non-matching OTPs
        total_no_match = 0
        for _ in range(iterations):
            start = time.perf_counter()
            verify_otp_constant_time("123456", "999999")
            total_no_match += time.perf_counter() - start
        avg_no_match = total_no_match / iterations

        # Times should be similar (within 2x when averaged)
        # This is a relaxed check since hmac.compare_digest is already constant-time
        time_ratio = max(avg_match, avg_no_match) / min(avg_match, avg_no_match)
        assert time_ratio < 2.0, f"Time ratio {time_ratio} suggests non-constant time"


class TestOTPExpiry:
    """Test OTP expiry."""

    def test_otp_not_expired(self):
        """Test OTP within expiry time."""
        created_at = datetime.utcnow()
        assert is_otp_expired(created_at, expiry_minutes=5) is False

    def test_otp_expired(self):
        """Test OTP past expiry time."""
        created_at = datetime.utcnow() - timedelta(minutes=10)
        assert is_otp_expired(created_at, expiry_minutes=5) is True


@pytest.mark.asyncio
class TestOTPRedis:
    """Test OTP Redis operations."""

    async def test_store_and_get_otp(self):
        """Test storing and retrieving OTP."""
        email = "test_store@example.com"
        otp = "123456"

        try:
            await store_otp(email, otp)
            data = await get_otp(email)

            assert data is not None
            assert data["otp"] == otp
            assert data["attempts"] == 0
        finally:
            # Cleanup
            await delete_otp(email)

    async def test_delete_otp(self):
        """Test deleting OTP."""
        email = "test_delete@example.com"
        otp = "123456"

        try:
            await store_otp(email, otp)
            await delete_otp(email)

            data = await get_otp(email)
            assert data is None
        except Exception:
            # Cleanup even if test fails
            await delete_otp(email)
            raise

    async def test_increment_attempts(self):
        """Test incrementing OTP attempts."""
        email = "test_increment@example.com"
        otp = "123456"

        try:
            await store_otp(email, otp)

            attempts = await increment_otp_attempts(email)
            assert attempts == 1

            attempts = await increment_otp_attempts(email)
            assert attempts == 2

            attempts = await increment_otp_attempts(email)
            assert attempts == 3

            # After max attempts, OTP should be deleted
            data = await get_otp(email)
            assert data is None
        finally:
            # Cleanup
            await delete_otp(email)


@pytest.mark.asyncio
class TestOTPEndpoints:
    """Test OTP API endpoints."""

    async def test_request_otp_sends_email(self, async_client, db, mocker):
        """Test that requesting an OTP triggers an email and stores OTP in Redis."""
        # This test assumes an endpoint `/api/v1/auth/request-otp` exists for
        # requesting an OTP code. If your endpoint is different, please adjust.

        # Mock the email sending function to prevent actual emails during tests
        # and to allow us to check if it was called.
        mock_send_otp_email = mocker.patch(
            "app.modules.auth.routes.send_otp_email", new_callable=AsyncMock
        )
        mock_send_otp_email.return_value = True

        email = "otp_request@example.com"
        user_name = "OTP Request User"

        # A user must exist to receive an OTP
        user = User(email=email, name=user_name, role=Role.CUSTOMER)
        db.add(user)
        db.commit()

        try:
            # Make a request to the endpoint that should trigger the OTP email
            response = await async_client.post("/api/v1/auth/request-otp", json={"email": email})

            # 1. Check if the endpoint returns a success status
            assert response.status_code == 200, "The request to the OTP endpoint failed."
            # NOTE: The response message might differ in your actual implementation.
            assert "OTP has been sent" in response.json().get(
                "message", ""
            ), "Success message not found in response."

            # 2. Check if the email sending function was called exactly once
            mock_send_otp_email.assert_called_once()

            # 3. Check that it was called with the correct arguments
            args, kwargs = mock_send_otp_email.call_args
            sent_to_email = args[0]
            sent_otp = args[1]
            sent_to_name = args[2]

            assert sent_to_email == email
            assert isinstance(sent_otp, str)
            assert len(sent_otp) == 6
            assert sent_otp.isdigit()
            assert sent_to_name == user_name

            # 4. Check if the sent OTP was correctly stored in Redis
            redis_data = await get_otp(email)
            assert redis_data is not None, "OTP was not found in Redis."
            assert redis_data["otp"] == sent_otp

        finally:
            # Clean up by deleting the OTP from Redis
            await delete_otp(email)

    async def test_verify_otp_success(self, async_client, db):
        """Test successful OTP verification."""
        # Setup: Create user and OTP
        email = "test_success@example.com"
        otp = "123456"

        # Create user
        user = User(email=email, name="Test User", role=Role.CUSTOMER)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Store OTP
        await store_otp(email, otp)

        try:
            # Verify OTP
            response = await async_client.post(
                "/api/v1/auth/verify-otp", json={"email": email, "otp": otp}
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == email
        finally:
            # Cleanup
            await delete_otp(email)

    async def test_verify_otp_invalid(self, async_client, db):
        """Test invalid OTP verification."""
        email = "test_invalid@example.com"

        # Create user
        user = User(email=email, name="Test User", role=Role.CUSTOMER)
        db.add(user)
        db.commit()

        # Store correct OTP
        await store_otp(email, "123456")

        try:
            # Try wrong OTP
            response = await async_client.post(
                "/api/v1/auth/verify-otp", json={"email": email, "otp": "999999"}
            )

            assert response.status_code == 400
            assert "Invalid verification code" in response.json()["detail"]
        finally:
            # Cleanup
            await delete_otp(email)

    async def test_verify_otp_expired(self, async_client, db):
        """Test expired OTP verification."""
        email = "test_expired@example.com"

        # Create user
        user = User(email=email, name="Test User", role=Role.CUSTOMER)
        db.add(user)
        db.commit()

        # Don't store OTP - it will be treated as expired/not found
        response = await async_client.post(
            "/api/v1/auth/verify-otp", json={"email": email, "otp": "123456"}
        )

        # Should return 400 for expired/not found OTP
        assert response.status_code == 400
        assert (
            "expired" in response.json()["detail"].lower()
            or "not found" in response.json()["detail"].lower()
        )

    async def test_verify_otp_max_attempts(self, async_client, db, mocker):
        """Test max attempts exceeded."""
        # Mock rate limit check to avoid 429 errors during this test
        # We want to test the OTP max attempts logic, not the API rate limiter
        mocker.patch(
            "app.modules.auth.routes.check_otp_rate_limit",
            return_value=True,
            new_callable=AsyncMock,
        )

        email = "test_maxattempts@example.com"
        correct_otp = "123456"

        # Create user
        user = User(email=email, name="Test User", role=Role.CUSTOMER)
        db.add(user)
        db.commit()

        # Store OTP
        await store_otp(email, correct_otp)

        try:
            # Try wrong OTP 3 times
            for i in range(3):
                response = await async_client.post(
                    "/api/v1/auth/verify-otp", json={"email": email, "otp": "999999"}
                )

                if i < 2:
                    # First 2 attempts should return remaining attempts
                    assert response.status_code == 400
                    assert "remaining" in response.json()["detail"].lower()
                else:
                    # 3rd attempt should say max attempts exceeded
                    assert response.status_code == 400
                    assert "maximum" in response.json()["detail"].lower()

            # Verify OTP is deleted after max attempts
            data = await get_otp(email)
            assert data is None
        finally:
            # Cleanup
            await delete_otp(email)

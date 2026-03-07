# backend/app/core/otp.py
"""
OTP generation and verification utilities.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta


def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure random OTP.

    Args:
        length: Number of digits (default: 6)

    Returns:
        String of random digits

    Example:
        >>> otp = generate_otp()
        >>> len(otp)
        6
        >>> otp.isdigit()
        True
    """
    if length < 4 or length > 10:
        raise ValueError("OTP length must be between 4 and 10 digits")

    # Use secrets module for cryptographic randomness
    # Range: 10^(n-1) to 10^n - 1
    # For n=6: 100000 to 999999
    min_value = 10 ** (length - 1)
    max_value = (10**length) - 1

    otp = secrets.randbelow(max_value - min_value + 1) + min_value
    return str(otp)


def hash_otp(otp: str, email: str) -> str:
    """
    Hash OTP with email as salt for additional security.

    Args:
        otp: The OTP to hash
        email: User's email (used as salt)

    Returns:
        Hex digest of hashed OTP

    Note:
        This is optional - for most use cases, storing OTP in Redis
        with TTL is sufficient. Use this if you need additional security.
    """
    return hashlib.sha256(f"{otp}:{email}".encode()).hexdigest()


def verify_otp_constant_time(stored_otp: str, provided_otp: str) -> bool:
    """
    Verify OTP using constant-time comparison to prevent timing attacks.

    Args:
        stored_otp: OTP from Redis/database
        provided_otp: OTP provided by user

    Returns:
        True if OTPs match, False otherwise

    Security:
        Uses hmac.compare_digest for constant-time comparison.
        This prevents timing attacks where attackers could determine
        correct digits by measuring response times.

    Example:
        >>> verify_otp_constant_time("123456", "123456")
        True
        >>> verify_otp_constant_time("123456", "654321")
        False
    """
    # Normalize inputs to fixed digest lengths before comparison.
    # This makes timing less sensitive to input length/content variance.
    stored_otp_str = "" if stored_otp is None else str(stored_otp)
    provided_otp_str = "" if provided_otp is None else str(provided_otp)

    stored_digest = hashlib.sha256(stored_otp_str.encode()).digest()
    provided_digest = hashlib.sha256(provided_otp_str.encode()).digest()
    digest_match = hmac.compare_digest(stored_digest, provided_digest)

    # Preserve original behavior: empty/missing OTPs are always invalid.
    return bool(stored_otp_str) and bool(provided_otp_str) and digest_match


def is_otp_expired(created_at: datetime, expiry_minutes: int = 5) -> bool:
    """
    Check if OTP has expired.

    Args:
        created_at: When OTP was created (UTC)
        expiry_minutes: Expiry time in minutes (default: 5)

    Returns:
        True if expired, False otherwise

    Example:
        >>> from datetime import datetime, timedelta
        >>> # OTP created 3 minutes ago
        >>> created = datetime.now(UTC) - timedelta(minutes=3)
        >>> is_otp_expired(created, expiry_minutes=5)
        False
        >>> # OTP created 10 minutes ago
        >>> created = datetime.now(UTC) - timedelta(minutes=10)
        >>> is_otp_expired(created, expiry_minutes=5)
        True
    """
    if not created_at:
        return True

    expiry_time = created_at + timedelta(minutes=expiry_minutes)
    return datetime.now(UTC) > expiry_time


def format_otp_for_display(otp: str, separator: str = " ") -> str:
    """
    Format OTP for better readability in emails/SMS.

    Args:
        otp: The OTP to format
        separator: Character to use between digit groups (default: space)

    Returns:
        Formatted OTP string

    Example:
        >>> format_otp_for_display("123456")
        '123 456'
        >>> format_otp_for_display("123456", separator="-")
        '123-456'
    """
    if len(otp) == 6:
        # Format as XXX XXX
        return f"{otp[:3]}{separator}{otp[3:]}"
    elif len(otp) == 4:
        # Format as XX XX
        return f"{otp[:2]}{separator}{otp[2:]}"
    else:
        # For other lengths, just return as-is
        return otp

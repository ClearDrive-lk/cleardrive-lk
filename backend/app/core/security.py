# backend/app/core/security.py

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, cast, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64

from .config import settings

# Password hashing context (Argon2id - most secure)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=8,
)

# Initialize Fernet encryption
try:
    fernet = Fernet(settings.ENCRYPTION_KEY.encode())
except Exception:
    # Fallback for invalid key during development
    print("⚠️  Warning: Invalid ENCRYPTION_KEY, generating temporary key")
    fernet = Fernet(Fernet.generate_key())


# ============================================================================
# PASSWORD HASHING
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return cast(str, pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return cast(bool, pwd_context.verify(plain_password, hashed_password))
    except Exception:
        return False


# ============================================================================
# JWT TOKEN GENERATION
# ============================================================================


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Dictionary of claims to encode
        expires_delta: Token expiration time (default: 30 minutes)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "type": "access",
            "jti": secrets.token_urlsafe(16),  # JWT ID for token tracking
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return cast(str, encoded_jwt)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Dictionary of claims to encode
        expires_delta: Token expiration time (default: 30 days)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh", "jti": secrets.token_urlsafe(16)})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return cast(str, encoded_jwt)


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return cast(dict[str, Any], payload)
    except JWTError:
        return None


# ============================================================================
# OTP GENERATION
# ============================================================================


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP (One-Time Password).

    Args:
        length: Length of OTP (default: 6 digits)

    Returns:
        Random OTP string
    """
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256 for secure storage.

    Args:
        token: Token string to hash

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(token.encode()).hexdigest()


def constant_time_compare(val1: str, val2: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.

    Args:
        val1: First string
        val2: Second string

    Returns:
        True if strings match, False otherwise
    """
    return secrets.compare_digest(val1.encode(), val2.encode())


# ============================================================================
# DATA ENCRYPTION (AES-256)
# ============================================================================


def encrypt_field(plain_text: str) -> Optional[str]:
    """
    Encrypt sensitive data using AES-256 (Fernet).

    Args:
        plain_text: Plain text to encrypt

    Returns:
        Base64-encoded encrypted string or None if input is None
    """
    if not plain_text:
        return None

    try:
        encrypted = fernet.encrypt(plain_text.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return None


def decrypt_field(encrypted_text: str) -> Optional[str]:
    """
    Decrypt sensitive data using AES-256 (Fernet).

    Args:
        encrypted_text: Base64-encoded encrypted string

    Returns:
        Decrypted plain text or None if input is None
    """
    if not encrypted_text:
        return None

    try:
        encrypted = base64.b64decode(encrypted_text.encode())
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None


# ============================================================================
# FILE INTEGRITY (SHA-256 Checksums)
# ============================================================================


def calculate_file_hash(content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content.

    Args:
        content: File content as bytes

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content).hexdigest()


def verify_file_integrity(content: bytes, expected_hash: str) -> bool:
    """
    Verify file integrity using SHA-256 checksum.

    Args:
        content: File content as bytes
        expected_hash: Expected SHA-256 hash

    Returns:
        True if file is intact, False if tampered
    """
    actual_hash = calculate_file_hash(content)
    return constant_time_compare(actual_hash, expected_hash)

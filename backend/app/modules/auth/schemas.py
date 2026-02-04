# backend/app/modules/auth/schemas.py

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .models import Role

# ============================================================================
# USER SCHEMAS
# ============================================================================


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""

    password: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""

    name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    role: Role
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# GOOGLE OAUTH SCHEMAS
# ============================================================================


class GoogleAuthRequest(BaseModel):
    """Google OAuth authentication request."""

    id_token: str = Field(..., description="Google ID token from client")


class GoogleAuthResponse(BaseModel):
    """Response after Google OAuth verification."""

    email: EmailStr
    name: Optional[str]
    google_id: str
    message: str = "OTP sent to email"


# ============================================================================
# OTP SCHEMAS
# ============================================================================


class OTPVerifyRequest(BaseModel):
    """OTP verification request."""

    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class OTPResendRequest(BaseModel):
    """OTP resend request."""

    email: EmailStr


class DevEnsureUserRequest(BaseModel):
    """Dev-only: ensure a test user exists (create if not)."""

    email: EmailStr
    name: Optional[str] = None


# ============================================================================
# TOKEN SCHEMAS
# ============================================================================


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: UUID
    email: str
    role: Role
    exp: datetime
    type: str
    jti: str


# ============================================================================
# SESSION SCHEMAS
# ============================================================================


class SessionResponse(BaseModel):
    """User session response."""

    id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[str]
    location: Optional[str]
    is_active: bool
    last_active: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """List of user sessions."""

    sessions: list[SessionResponse]
    total: int
    current_session_id: UUID


# ============================================================================
# AUTH STATUS SCHEMAS
# ============================================================================


class AuthStatusResponse(BaseModel):
    """Current authentication status."""

    authenticated: bool
    user: Optional[UserResponse] = None

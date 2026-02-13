# backend/app/modules/auth/schemas.py

from datetime import datetime
from typing import List, Optional
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
    role: Optional[Role] = None


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


class SessionLocation(BaseModel):
    """Geographic location information."""

    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SessionInfo(BaseModel):
    """Session information model for API response."""

    session_id: str = Field(..., description="Unique session identifier")
    ip_address: str = Field(..., description="IP address of the session")
    device_type: str = Field(..., description="Device type: Mobile, Tablet, PC")
    device_name: str = Field(..., description="Device model or name")
    browser: str = Field(..., description="Browser name and version")
    os: str = Field(..., description="Operating system and version")
    location: Optional[SessionLocation] = Field(None, description="Geographic location")
    created_at: str = Field(..., description="Session creation timestamp (ISO 8601)")
    last_active: str = Field(..., description="Last activity timestamp (ISO 8601)")
    is_current: bool = Field(False, description="Whether this is the current session")


class SessionsResponse(BaseModel):
    """Response model for active sessions list."""

    sessions: List[SessionInfo] = Field(..., description="List of active sessions")
    total: int = Field(..., description="Total number of active sessions")
    limit: int = Field(..., description="Maximum allowed sessions per user")


class SessionRevokeResponse(BaseModel):
    """Response model for session revocation."""

    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="ID of revoked session")


class AllSessionsRevokeResponse(BaseModel):
    """Response model for revoking all sessions."""

    message: str = Field(..., description="Success message")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")
    note: str = Field(..., description="Important note for user")


# ============================================================================
# AUTH STATUS SCHEMAS
# ============================================================================


class AuthStatusResponse(BaseModel):
    """Current authentication status."""

    authenticated: bool
    user: Optional[UserResponse] = None

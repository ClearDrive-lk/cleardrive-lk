# backend/app/modules/auth/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any, Optional, cast, Dict
import httpx
from uuid import UUID
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    hash_token,
    constant_time_compare,
)
from app.core.dependencies import get_current_active_user
from app.core.redis_client import get_redis
from app.core.config import settings

from .models import User, Session as UserSession, Role
from .schemas import (
    GoogleAuthRequest,
    GoogleAuthResponse,
    OTPVerifyRequest,
    OTPResendRequest,
    DevEnsureUserRequest,
    TokenResponse,
    RefreshTokenRequest,
    SessionListResponse,
    SessionResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# GOOGLE OAUTH - IMPROVED VERSION
# ============================================================================


@router.post("/google", response_model=GoogleAuthResponse)
async def google_auth(
    auth_request: GoogleAuthRequest,
    request: Request,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Authenticate with Google OAuth2.

    Steps:
    1. Verify Google ID token
    2. Create/update user
    3. Generate OTP
    4. Send OTP via email (simulated for now)
    5. Return user info
    """

    # Verify Google ID token
    try:
        google_user_info = verify_google_token_v2(auth_request.id_token)
    except Exception as e:
        err_msg = str(e)
        if "4166288126" in err_msg:
            err_msg += (
                " (Hint: You are using the default OAuth Playground credentials! Click Gear icon ⚙️ → "
                "'Use your own OAuth credentials' → Enter your Client ID/Secret.)"
            )
        elif "wrong audience" in err_msg.lower():
            err_msg += " (Hint: Check that GOOGLE_CLIENT_ID in backend/.env matches the Client ID used to generate the token!)"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err_msg)

    email = google_user_info.get("email")
    google_id = google_user_info.get("sub")
    name = google_user_info.get("name")
    email_verified = google_user_info.get("email_verified", False)

    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token payload",
        )

    # Require verified email
    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified with Google. Please verify your email first.",
        )

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            role=Role.CUSTOMER,
        )

        # Check if this should be an admin (first user from ADMIN_EMAILS)
        admin_emails = [e.strip() for e in settings.ADMIN_EMAILS.split(",")]
        if email in admin_emails:
            # Check if any admin exists
            existing_admin = db.query(User).filter(User.role == Role.ADMIN).first()
            if not existing_admin:
                user.role = Role.ADMIN
                print(f"🔐 Auto-promoted first admin: {email}")

        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✅ New user created: {email} (Role: {user.role})")
    else:
        # Update existing user's Google ID if not set
        if not user.google_id:
            user.google_id = google_id
            db.commit()

        print(f"✅ Existing user logged in: {email}")

    # Generate OTP
    otp = generate_otp()

    # Store OTP in Redis (5-minute expiry)
    otp_key = f"otp:{email}"
    await redis.setex(otp_key, 300, otp)  # 300 seconds = 5 minutes

    # TODO: Send OTP via email (we'll implement this in notifications module)
    # For now, log it (ONLY IN DEVELOPMENT!)
    if settings.ENVIRONMENT == "development":
        print(f"\n{'='*60}")
        print(f"🔐 OTP for {email}: {otp}")
        print(f"{'='*60}\n")

    return GoogleAuthResponse(
        email=email,
        name=name,
        google_id=google_id,
        message="OTP sent to your email. Check console in development mode.",
    )


def verify_google_token_v2(id_token_string: str) -> Dict[str, Any]:
    """
    Verify Google ID token using official Google library.

    This is the PROPER way to verify Google tokens.

    Args:
        id_token_string: Google ID token from client

    Returns:
        User info from Google

    Raises:
        ValueError: If token is invalid
    """
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            id_token_string, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        # Additional checks
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")

        # Token is valid
        return cast(Dict[str, Any], idinfo)

    except ValueError as e:
        # Invalid token
        raise ValueError(f"Invalid Google token: {str(e)}")


async def verify_google_token(id_token: str) -> Dict[str, Any]:
    """
    Verify Google ID token with Google API (fallback method).

    Args:
        id_token: Google ID token from client

    Returns:
        User info from Google

    Raises:
        Exception: If token is invalid
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token}
        )

        if response.status_code != 200:
            raise Exception("Invalid Google token")

        user_info = cast(Dict[str, Any], response.json())

        # Verify audience (client ID)
        if user_info.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise Exception("Invalid token audience")

        return user_info  # type: ignore


# ============================================================================
# OTP VERIFICATION
# ============================================================================


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    verify_request: OTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Verify OTP and issue JWT tokens.

    Steps:
    1. Verify OTP from Redis
    2. Generate access & refresh tokens
    3. Create session
    4. Return tokens
    """

    # Get OTP from Redis
    otp_key = f"otp:{verify_request.email}"
    stored_otp = await redis.get(otp_key)

    if not stored_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired or not found. Please request a new one.",
        )

    # Verify OTP (constant-time comparison to prevent timing attacks)
    if not constant_time_compare(verify_request.otp, stored_otp):
        # Increment failed attempts
        user = db.query(User).filter(User.email == verify_request.email).first()
        if user:
            user.failed_auth_attempts += 1
            user.last_failed_auth = datetime.utcnow()
            db.commit()

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    # Delete OTP (one-time use)
    await redis.delete(otp_key)

    # Get user
    user = db.query(User).filter(User.email == verify_request.email).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Reset failed attempts on successful login
    user.failed_auth_attempts = 0
    user.last_failed_auth = None
    db.commit()

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Create session
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        device_info=extract_device_info(request),
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(session)

    # Check session limit (max 5 sessions)
    session_count = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.is_active == True)
        .count()
    )

    if session_count > 5:
        # Revoke oldest session
        oldest_session = (
            db.query(UserSession)
            .filter(UserSession.user_id == user.id, UserSession.is_active == True)
            .order_by(UserSession.created_at.asc())
            .first()
        )

        if oldest_session:
            oldest_session.is_active = False

    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/resend-otp")
async def resend_otp(
    resend_request: OTPResendRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """Resend OTP to user's email."""

    # Check if user exists
    user = db.query(User).filter(User.email == resend_request.email).first()

    if not user:
        # Don't reveal if email exists or not (security)
        return {"message": "If the email exists, OTP has been sent"}

    # Generate new OTP
    otp = generate_otp()

    # Store in Redis
    otp_key = f"otp:{resend_request.email}"
    await redis.setex(otp_key, 300, otp)

    # TODO: Send via email
    if settings.ENVIRONMENT == "development":
        print(f"🔐 OTP for {resend_request.email}: {otp}")
        return {"message": "If the email exists, OTP has been sent", "otp": otp}

    return {"message": "If the email exists, OTP has been sent"}


# ============================================================================
# DEV-ONLY: ENSURE TEST USER (for scripts / local testing)
# ============================================================================


@router.post("/dev/ensure-user")
async def dev_ensure_user(
    body: DevEnsureUserRequest,
    db: Session = Depends(get_db),
):
    """
    Create a test user if they don't exist. Only available when ENVIRONMENT=development.
    Use before resend-otp when testing so OTP is actually stored.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        return {"created": False, "email": body.email, "message": "User already exists"}
    name = body.name or body.email.split("@")[0]
    user = User(email=body.email, name=name, role=Role.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "created": True,
        "email": body.email,
        "name": name,
        "message": "User created",
    }


# ============================================================================
# TOKEN REFRESH
# ============================================================================


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Implements token rotation - old refresh token is invalidated.
    """

    # Decode refresh token
    payload = decode_token(refresh_request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")

    # Get user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Find session with this refresh token
    refresh_token_hash = hash_token(refresh_request.refresh_token)
    session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user.id,
            UserSession.refresh_token_hash == refresh_token_hash,
            UserSession.is_active == True,
        )
        .first()
    )

    if not session:
        # Token reuse detected! Revoke ALL user sessions
        db.query(UserSession).filter(
            UserSession.user_id == user.id, UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. All sessions revoked.",
        )

    # Generate new tokens (rotation)
    new_access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Update session with new refresh token
    session.refresh_token_hash = hash_token(new_refresh_token)
    session.last_active = datetime.utcnow()

    db.commit()

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all active sessions for current user."""

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active == True)
        .order_by(UserSession.last_active.desc())
        .all()
    )

    # Get current session ID from token (would need to pass it somehow)
    # For now, use the most recent session
    current_session_id = sessions[0].id if sessions else None

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=len(sessions),
        current_session_id=current_session_id,
    )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Revoke a specific session."""

    session = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    session.is_active = False
    db.commit()

    return {"message": "Session revoked successfully"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Logout current user (revoke current session)."""

    # In a real app, we'd get the session ID from the token's jti claim
    # For now, revoke the most recent session

    recent_session = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active == True)
        .order_by(UserSession.last_active.desc())
        .first()
    )

    if recent_session:
        recent_session.is_active = False
        db.commit()

    return {"message": "Logged out successfully"}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def extract_device_info(request: Request) -> Optional[str]:
    """Extract device info from user agent."""
    user_agent = request.headers.get("user-agent", "")

    if "Mobile" in user_agent:
        return "Mobile"
    elif "Tablet" in user_agent:
        return "Tablet"
    else:
        return "Desktop"

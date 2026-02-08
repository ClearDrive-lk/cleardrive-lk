# backend/app/modules/auth/routes.py

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast
from uuid import UUID

import httpx
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.otp import generate_otp
from app.core.redis import (
    blacklist_token,
    check_otp_rate_limit,
    create_session,
    delete_all_user_sessions,
    delete_otp,
    delete_refresh_token,
    enforce_session_limit,
    get_otp,
    get_redis,
    increment_otp_attempts,
    is_token_blacklisted,
    store_otp,
    store_refresh_token,
)
from app.core.security import (
    constant_time_compare,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
)
from app.services.email import send_otp_email
from fastapi import APIRouter, Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

# Import OTP helper if it exists
try:
    from app.core.otp import verify_otp_constant_time
except ImportError:
    verify_otp_constant_time = None  # type: ignore

from .models import Role
from .models import Session as UserSession
from .models import User
from .schemas import (
    DevEnsureUserRequest,
    GoogleAuthRequest,
    GoogleAuthResponse,
    OTPResendRequest,
    OTPVerifyRequest,
    RefreshTokenRequest,
    SessionListResponse,
    SessionResponse,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
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
                " (Hint: You are using the default OAuth Playground credentials! "
                "Click Gear icon ⚙️ → 'Use your own OAuth credentials' → "
                "Enter your Client ID/Secret.)"
            )
        elif "wrong audience" in err_msg.lower():
            err_msg += (
                " (Hint: Check that GOOGLE_CLIENT_ID in backend/.env matches the "
                "Client ID used to generate the token!)"
            )
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
                logger.info(f"Auto-promoted first admin: {email}")

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"New user created: {email} (Role: {user.role})")
    else:
        # Update existing user's Google ID if not set
        if not user.google_id:
            user.google_id = google_id
            db.commit()

        logger.info(f"Existing user logged in: {email}")

    # Generate OTP
    otp = generate_otp()

    # Store OTP in Redis (5-minute expiry)
    await store_otp(email, otp)

    # Send OTP via email
    email_sent = await send_otp_email(email, otp, name)

    if not email_sent:
        logger.error(f"Failed to send OTP email to {email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code. Please try again.",
        )

    return GoogleAuthResponse(
        email=email,
        name=name,
        google_id=google_id,
        message="Verification code sent to your email",
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
# OTP VERIFICATION - UNIFIED VERSION
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

    Rate Limit: 3 requests per 5 minutes per email
    Max Attempts: 3 attempts per OTP

    Steps:
    1. Check rate limit
    2. Verify OTP from Redis
    3. Generate access & refresh tokens
    4. Store refresh token metadata in Redis
    5. Create Redis session
    6. Create database session
    7. Enforce session limits
    8. Return tokens

    Args:
        verify_request: Email and OTP
        request: HTTP request (for IP/device info)
        db: Database session
        redis: Redis client

    Returns:
        JWT tokens and user info

    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 400: Invalid OTP or expired
        HTTPException 401: Invalid OTP
        HTTPException 404: User not found
    """

    # ========================================================================
    # STEP 1: Rate Limiting
    # ========================================================================
    if settings.ENVIRONMENT != "development":
        if not await check_otp_rate_limit(verify_request.email):
            logger.warning(f"OTP verification rate limit exceeded for {verify_request.email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification attempts. Please try again in 5 minutes.",
            )
    else:
        logger.debug(f"Skipping OTP rate limit in development for {verify_request.email}")

    # ========================================================================
    # STEP 2: Retrieve and Validate OTP
    # ========================================================================
    otp_data = await get_otp(verify_request.email)

    if not otp_data:
        logger.warning(f"No OTP found for {verify_request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired or not found. Please request a new one.",
        )

    # Check max attempts
    if otp_data.get("attempts", 0) >= 3:
        logger.warning(f"Max OTP attempts exceeded for {verify_request.email}")
        await delete_otp(verify_request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum verification attempts exceeded. Please request a new code.",
        )

    stored_otp = otp_data.get("otp")

    # Verify OTP (constant-time comparison to prevent timing attacks)
    verification_func = (
        verify_otp_constant_time if verify_otp_constant_time is not None else constant_time_compare
    )

    if not verification_func(cast(str, stored_otp), verify_request.otp):
        # Increment failed attempts
        attempts = await increment_otp_attempts(verify_request.email)
        logger.warning(f"Invalid OTP for {verify_request.email}. Attempt {attempts}/3")

        remaining = 3 - attempts
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {remaining} attempts remaining.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new code.",
            )

    # OTP verified successfully - delete it (one-time use)
    await delete_otp(verify_request.email)

    logger.info(f"OTP verified successfully for {verify_request.email}")

    # ========================================================================
    # STEP 3: Get User
    # ========================================================================
    user = db.query(User).filter(User.email == verify_request.email).first()

    if not user:
        logger.error(f"User not found after OTP verification: {verify_request.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Reset failed attempts on successful login
    user.failed_auth_attempts = 0
    user.last_failed_auth = None
    db.commit()

    # ========================================================================
    # STEP 4: Generate JWT Tokens
    # ========================================================================
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )

    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # ========================================================================
    # STEP 5: Decode Tokens to Get JTIs
    # ========================================================================
    refresh_payload = decode_refresh_token(refresh_token)

    refresh_jti = refresh_payload.get("jti") if refresh_payload else None

    # ========================================================================
    # STEP 6: Store Refresh Token Metadata in Redis
    # ========================================================================
    if refresh_jti:
        await store_refresh_token(
            token_jti=refresh_jti,
            user_id=str(user.id),
            device_info={
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # ====================================================================
        # STEP 7: Create Redis Session
        # ====================================================================
        session_id = str(uuid.uuid4())
        await create_session(
            user_id=str(user.id),
            session_id=session_id,
            token_jti=refresh_jti,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        # ====================================================================
        # STEP 8: Enforce Session Limit (max 5 concurrent sessions)
        # ====================================================================
        await enforce_session_limit(str(user.id), max_sessions=5)

    # ========================================================================
    # STEP 9: Create Database Session
    # ========================================================================
    db_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        device_info=extract_device_info(request),
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(db_session)

    # ========================================================================
    # STEP 10: Enforce Database Session Limit (max 5 sessions)
    # ========================================================================
    session_count = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
        .count()
    )

    if session_count > 5:
        # Revoke oldest session
        oldest_session = (
            db.query(UserSession)
            .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
            .order_by(UserSession.created_at.asc())
            .first()
        )

        if oldest_session:
            oldest_session.is_active = False
            logger.info(f"Revoked oldest session for {user.email} (session limit exceeded)")

    db.commit()

    # ========================================================================
    # STEP 11: Log Successful Authentication
    # ========================================================================
    logger.info(
        f"User authenticated successfully: {user.email}",
        extra={
            "user_id": str(user.id),
            "role": user.role.value,
            "session_id": session_id if refresh_jti else None,
        },
    )

    # ========================================================================
    # STEP 12: Return Tokens and User Info
    # ========================================================================
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
    """
    Resend OTP to user's email.

    Security: Returns same message whether email exists or not.
    """

    # Check if user exists
    user = db.query(User).filter(User.email == resend_request.email).first()

    if not user:
        # Don't reveal if email exists or not (security)
        logger.warning(f"OTP resend requested for non-existent email: {resend_request.email}")
        return {"message": "If the email exists, OTP has been sent"}

    # Generate new OTP
    otp = generate_otp()

    # Store in Redis
    await store_otp(resend_request.email, otp)

    logger.info(f"OTP resent for {resend_request.email}")

    # Send OTP via email
    await send_otp_email(resend_request.email, otp, user.name)

    if settings.ENVIRONMENT == "development":
        logger.info(f"🔐 OTP for {resend_request.email}: {otp}")
        return {"message": "If the email exists, OTP has been sent", "otp": otp}

    return {"message": "If the email exists, OTP has been sent"}


@router.post("/request-otp")
async def request_otp(
    request_data: OTPResendRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Request OTP for email login.
    """
    return await resend_otp(request_data, db, redis)


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
        logger.info(f"Dev: User already exists: {body.email}")
        return {"created": False, "email": body.email, "message": "User already exists"}

    name = body.name or body.email.split("@")[0]
    user = User(email=body.email, name=name, role=Role.CUSTOMER)
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"Dev: User created: {body.email}")

    return {
        "created": True,
        "email": body.email,
        "name": name,
        "message": "User created",
    }


# ============================================================================
# TOKEN REFRESH - ENHANCED WITH SECURITY
# ============================================================================


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Token Rotation:
    1. Validate old refresh token
    2. Generate NEW token pair
    3. Blacklist OLD refresh token
    4. Return NEW tokens

    Security:
    - Token reuse detection (if old token used twice)
    - Automatic session revocation on reuse
    - Token blacklisting to prevent replay attacks

    Args:
        refresh_request: Refresh token request
        request: HTTP request (for IP, user agent)
        db: Database session

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException 401: Invalid or expired refresh token
        HTTPException 403: Token reuse detected
        HTTPException 404: User not found
    """
    try:
        # Decode refresh token
        payload = decode_refresh_token(refresh_request.refresh_token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("sub")
        token_jti = payload.get("jti")
        exp_timestamp = payload.get("exp")

        if not user_id or not token_jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Check if token is blacklisted (TOKEN REUSE DETECTION)
        if await is_token_blacklisted(token_jti):
            # 🚨 SECURITY ALERT: Token reuse detected!
            logger.critical(
                f"SECURITY ALERT: Refresh token reuse detected for user {user_id}",
                extra={
                    "user_id": user_id,
                    "token_jti": token_jti,
                    "ip": request.client.host if request.client else "unknown",
                    "security_event": "token_reuse",
                },
            )

            # Revoke ALL user sessions (security measure)
            revoked_count = await delete_all_user_sessions(user_id)

            # Also revoke all database sessions
            (
                db.query(UserSession)
                .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
                .update({"is_active": False})
            )
            db.commit()

            log_msg = (
                f"Revoked {revoked_count} Redis sessions + DB sessions "
                f"for user {user_id} due to token reuse"
            )
            logger.warning(log_msg)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Token reuse detected. All sessions have been revoked. " "Please sign in again."
                ),
            )

        # Get user
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.error(f"User not found during token refresh: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Find database session with this refresh token
        refresh_token_hash = hash_token(refresh_request.refresh_token)
        session = (
            db.query(UserSession)
            .filter(
                UserSession.user_id == user.id,
                UserSession.refresh_token_hash == refresh_token_hash,
                UserSession.is_active.is_(True),
            )
            .first()
        )

        if not session:
            # Token not found in database - possible reuse
            logger.warning(
                f"Refresh token not found in database for user {user.email}. Possible token reuse."
            )
            # Don't revoke all sessions here since blacklist already caught it
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Generate NEW tokens (rotation)
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Decode new refresh token to get its JTI
        new_payload = decode_refresh_token(new_refresh_token)
        new_token_jti = new_payload.get("jti") if new_payload else None

        # Blacklist OLD refresh token (prevent reuse)
        # TTL = remaining token lifetime
        if exp_timestamp:
            remaining_seconds = exp_timestamp - datetime.utcnow().timestamp()
            if remaining_seconds > 0:
                await blacklist_token(token_jti, int(remaining_seconds))

        # Delete old refresh token metadata from Redis
        await delete_refresh_token(token_jti)

        # Store NEW refresh token metadata in Redis
        if new_token_jti:
            await store_refresh_token(
                token_jti=new_token_jti,
                user_id=str(user.id),
                device_info={
                    "ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                },
            )

            # Create new Redis session
            session_id = str(uuid.uuid4())
            await create_session(
                user_id=str(user.id),
                session_id=session_id,
                token_jti=new_token_jti,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
            )

        # Update database session with new refresh token
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.last_active = datetime.utcnow()
        db.commit()

        logger.info(
            f"Token refreshed successfully for user {user.email}",
            extra={"user_id": str(user.id)},
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
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
        .filter(UserSession.user_id == current_user.id, UserSession.is_active.is_(True))
        .order_by(UserSession.last_active.desc())
        .all()
    )

    # Get current session ID from token (would need to pass it somehow)
    # For now, use the most recent session
    current_session_id = sessions[0].id if sessions else None

    logger.info(f"Retrieved {len(sessions)} active sessions for user {current_user.email}")

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

    logger.info(f"Session {session_id} revoked for user {current_user.email}")

    return {"message": "Session revoked successfully"}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Logout user and blacklist tokens.

    Actions:
    1. Extract token JTI from current request
    2. Blacklist current access token
    3. Delete current session from Redis
    4. Revoke current session in database

    Security:
    - Prevents token reuse after logout
    - Clears all session data
    - Immediate token invalidation

    Args:
        request: HTTP request (to extract token)
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message with sessions cleared count
    """

    # Get token JTI from request state (set during authentication)
    token_jti = getattr(request.state, "token_jti", None)

    logger.info(f"Logout requested for user {current_user.id} (JTI: {token_jti})")

    if token_jti:
        # Blacklist access token
        # TTL = remaining token lifetime (max 30 minutes for access tokens)
        await blacklist_token(token_jti, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        logger.info(
            f"Access token blacklisted for user {current_user.email}",
            extra={"user_id": str(current_user.id), "token_jti": token_jti},
        )

    # Delete all Redis sessions for this user
    deleted_redis_sessions = await delete_all_user_sessions(str(current_user.id))

    # Revoke all database sessions
    db_sessions_updated = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active.is_(True))
        .update({"is_active": False}, synchronize_session=False)
    )
    db.commit()

    logger.info(
        f"User logged out: {current_user.email}. "
        f"Deleted {deleted_redis_sessions} Redis sessions, "
        f"revoked {db_sessions_updated} DB sessions.",
        extra={
            "user_id": str(current_user.id),
            "redis_sessions": deleted_redis_sessions,
            "db_sessions": db_sessions_updated,
        },
    )

    return {
        "message": "Logged out successfully",
        "sessions_cleared": deleted_redis_sessions + db_sessions_updated,
    }


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

# backend/app/modules/auth/routes.py

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast

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
    delete_session,
    enforce_session_limit,
    get_otp,
    get_redis,
    get_user_sessions,
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
    hash_password,
    hash_token,
    verify_password,
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

# Import session helpers if they exist
try:
    from app.core.session import detect_suspicious_activity, extract_session_metadata
except ImportError:
    extract_session_metadata = None  # type: ignore
    detect_suspicious_activity = None  # type: ignore

from .models import Role
from .models import Session as UserSession
from .models import User
from .schemas import (
    AllSessionsRevokeResponse,
    DevEnsureUserRequest,
    ForgotPasswordRequest,
    GoogleAuthRequest,
    GoogleAuthResponse,
    LoginRequest,
    OTPResendRequest,
    OTPVerifyRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionInfo,
    SessionLocation,
    SessionRevokeResponse,
    SessionsResponse,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# GOOGLE OAUTH
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
    4. Send OTP via email
    5. Return user info
    """
    try:
        google_user_info = verify_google_token_v2(auth_request.id_token)
    except Exception as e:
        err_msg = str(e)
        if "4166288126" in err_msg:
            err_msg += (
                " (Hint: You are using the default OAuth Playground credentials! "
                "Click Gear icon âš™ï¸ â†’ 'Use your own OAuth credentials' â†’ "
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

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified with Google. Please verify your email first.",
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            role=Role.CUSTOMER,
        )

        admin_emails = [e.strip() for e in settings.ADMIN_EMAILS.split(",")]
        if email in admin_emails:
            existing_admin = db.query(User).filter(User.role == Role.ADMIN).first()
            if not existing_admin:
                user.role = Role.ADMIN
                logger.info(f"Auto-promoted first admin: {email}")

        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created: {email} (Role: {user.role})")
    else:
        if not user.google_id:
            user.google_id = google_id
            db.commit()
        logger.info(f"Existing user logged in: {email}")

    otp = generate_otp()
    await store_otp(email, otp)

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
    """Verify Google ID token using official Google library."""
    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_string, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )

        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer.")

        return cast(Dict[str, Any], idinfo)

    except ValueError as e:
        raise ValueError(f"Invalid Google token: {str(e)}")


async def verify_google_token(id_token: str) -> Dict[str, Any]:
    """Verify Google ID token with Google API (fallback method)."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token}
        )

        if response.status_code != 200:
            raise Exception("Invalid Google token")

        user_info = cast(Dict[str, Any], response.json())

        if user_info.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise Exception("Invalid token audience")

        return user_info  # type: ignore


# ============================================================================
# OTP VERIFICATION - WITH SESSION METADATA + SUSPICIOUS ACTIVITY DETECTION
# ============================================================================


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    verify_request: OTPVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Verify OTP and issue JWT tokens with session tracking.

    Rate Limit: 3 requests per 5 minutes per email
    Max Attempts: 3 attempts per OTP

    Flow:
    1.  Check rate limit
    2.  Verify OTP from Redis
    3.  Get user
    4.  Extract session metadata (IP, device, location)
    5.  Detect suspicious activity (impossible travel, etc.)
    6.  Generate JWT tokens (access + refresh)
    7.  Store refresh token metadata in Redis
    8.  Create session with full metadata
    9.  Enforce Redis session limit (max 5)
    10. Create database session
    11. Enforce database session limit (max 5)
    12. Return tokens
    """

    # ========================================================================
    # STEP 1: Rate Limiting
    # ========================================================================
    if settings.ENVIRONMENT != "development":
        if not await check_otp_rate_limit(verify_request.email):
            logger.warning(f"OTP rate limit exceeded for {verify_request.email}")
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

    if otp_data.get("attempts", 0) >= 3:
        logger.warning(f"Max OTP attempts exceeded for {verify_request.email}")
        await delete_otp(verify_request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum verification attempts exceeded. Please request a new code.",
        )

    stored_otp = otp_data.get("otp")

    verification_func = (
        verify_otp_constant_time if verify_otp_constant_time is not None else constant_time_compare
    )

    if not verification_func(cast(str, stored_otp), verify_request.otp):
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

    await delete_otp(verify_request.email)
    logger.info(f"OTP verified successfully for {verify_request.email}")

    # ========================================================================
    # STEP 3: Get User
    # ========================================================================
    user = db.query(User).filter(User.email == verify_request.email).first()

    if not user:
        logger.error(f"User not found after OTP verification: {verify_request.email}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.failed_auth_attempts = 0
    user.last_failed_auth = None
    db.commit()

    # ========================================================================
    # STEP 4: Extract Session Metadata
    # ========================================================================
    logger.info(f"Extracting session metadata for user {user.email}")

    if extract_session_metadata is not None:
        session_metadata = extract_session_metadata(
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            include_location=True,
        )
        logger.debug(
            f"Session metadata extracted: {session_metadata.get('device_type')}, "
            f"{session_metadata.get('browser')}, "
            f"{session_metadata.get('location', {}).get('city', 'Unknown')}"
        )
    else:
        # Fallback if session module not available
        session_metadata = {
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "device_type": extract_device_info(request),
            "device_name": "Unknown Device",
            "browser": "Unknown",
            "os": "Unknown",
            "location": None,
        }

    # ========================================================================
    # STEP 5: Detect Suspicious Activity
    # ========================================================================
    if detect_suspicious_activity is not None:
        existing_sessions = await get_user_sessions(str(user.id))

        suspicious = detect_suspicious_activity(
            user_id=str(user.id),
            new_session_metadata=session_metadata,
            existing_sessions=existing_sessions,
        )

        if suspicious.get("is_suspicious"):
            logger.warning(
                f"âš ï¸ SUSPICIOUS LOGIN DETECTED for user {user.email}: "
                f"{', '.join(suspicious.get('reasons', []))}",
                extra={
                    "user_id": str(user.id),
                    "security_event": "suspicious_login",
                    "reasons": suspicious.get("reasons"),
                    "details": suspicious.get("details"),
                },
            )
            # Optional: await send_security_alert_email(...)
            # Optional: raise HTTPException(403, "Suspicious activity detected.")

    # ========================================================================
    # STEP 6: Generate JWT Tokens
    # ========================================================================
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # ========================================================================
    # STEP 7: Decode Refresh Token to Get JTI
    # ========================================================================
    refresh_payload = decode_refresh_token(refresh_token)
    refresh_jti = refresh_payload.get("jti") if refresh_payload else None

    session_id = None
    limit_result = {}

    if refresh_jti:
        # ====================================================================
        # STEP 7a: Store Refresh Token Metadata in Redis
        # ====================================================================
        await store_refresh_token(
            token_jti=refresh_jti,
            user_id=str(user.id),
            device_info={
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # ====================================================================
        # STEP 8: Create Redis Session with Full Metadata
        # ====================================================================
        session_id = str(uuid.uuid4())
        logger.info(f"Creating session {session_id} for user {user.email}")

        await create_session(
            user_id=str(user.id),
            session_id=session_id,
            token_jti=refresh_jti,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        # ====================================================================
        # STEP 9: Enforce Redis Session Limit (max 5)
        # ====================================================================
        limit_result = await enforce_session_limit(str(user.id), max_sessions=5)

        if limit_result.get("sessions_deleted", 0) > 0:
            logger.info(
                f"Session limit enforced: deleted {limit_result['sessions_deleted']} "
                f"old sessions for user {user.email}"
            )

    # ========================================================================
    # STEP 10: Create Database Session
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
    # STEP 11: Enforce Database Session Limit (max 5)
    # ========================================================================
    session_count = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
        .count()
    )

    if session_count > 5:
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
    # STEP 12: Log and Return
    # ========================================================================
    logger.info(
        f"âœ… Authentication successful for user {user.email}. "
        f"Session {session_id or 'N/A'} created. "
        f"Active sessions: {limit_result.get('current_count', 'N/A')}/"
        f"{limit_result.get('limit', 5)}",
        extra={
            "user_id": str(user.id),
            "role": user.role.value,
            "session_id": session_id,
        },
    )

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
    """Resend OTP to user's email. Returns same message whether email exists or not."""
    user = db.query(User).filter(User.email == resend_request.email).first()

    if not user:
        logger.warning(f"OTP resend requested for non-existent email: {resend_request.email}")
        return {"message": "If the email exists, OTP has been sent"}

    otp = generate_otp()
    await store_otp(resend_request.email, otp)
    logger.info(f"OTP resent for {resend_request.email}")

    await send_otp_email(resend_request.email, otp, user.name)

    if settings.ENVIRONMENT == "development":
        logger.info(f"ðŸ” OTP for {resend_request.email}: {otp}")
        return {"message": "If the email exists, OTP has been sent", "otp": otp}

    return {"message": "If the email exists, OTP has been sent"}


@router.post("/request-otp")
async def request_otp(
    request_data: OTPResendRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """Request OTP for email login."""
    return await resend_otp(request_data, db, redis)


@router.post("/forgot-password")
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Request OTP for password reset.

    Returns a generic success message to avoid account enumeration.
    """
    user = db.query(User).filter(User.email == request_data.email).first()

    if not user:
        logger.warning(f"Password reset requested for non-existent email: {request_data.email}")
        return {"message": "If the email exists, a reset code has been sent"}

    otp = generate_otp()
    await store_otp(request_data.email, otp)
    email_sent = await send_otp_email(request_data.email, otp, user.name)

    if not email_sent:
        logger.error(f"Failed to send password reset OTP to {request_data.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset code. Please try again.",
        )

    if settings.ENVIRONMENT == "development":
        logger.info(f"Password reset OTP for {request_data.email}: {otp}")
        return {
            "message": "If the email exists, a reset code has been sent",
            "otp": otp,
        }

    return {"message": "If the email exists, a reset code has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """Reset password using email, OTP and new password."""
    email = reset_request.email.strip().lower()
    otp_data = await get_otp(email)

    if not otp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired or not found. Please request a new code.",
        )

    if otp_data.get("attempts", 0) >= 3:
        await delete_otp(email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum verification attempts exceeded. Please request a new code.",
        )

    stored_otp = otp_data.get("otp")
    verification_func = (
        verify_otp_constant_time if verify_otp_constant_time is not None else constant_time_compare
    )
    if not verification_func(cast(str, stored_otp), reset_request.otp):
        attempts = await increment_otp_attempts(email)
        remaining = 3 - attempts
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {remaining} attempts remaining.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum verification attempts exceeded. Please request a new code.",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        await delete_otp(email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(reset_request.new_password)
    user.failed_auth_attempts = 0
    user.last_failed_auth = None
    db.commit()
    await delete_otp(email)

    # Security hygiene: invalidate active sessions after password change.
    await delete_all_user_sessions(str(user.id))
    (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.is_active.is_(True))
        .update({"is_active": False}, synchronize_session=False)
    )
    db.commit()

    logger.info(f"Password reset successful for {email}")
    return {"message": "Password reset successful. Please sign in again."}


@router.post("/login")
async def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Email/password login step.

    Validates credentials and then sends OTP for second-factor verification.
    """
    email = login_request.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    # Keep message generic to avoid account enumeration.
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    if not user or not user.password_hash:
        logger.warning(f"Login failed for {email}: user not found or no password set")
        raise invalid_credentials_error

    if not verify_password(login_request.password, user.password_hash):
        user.failed_auth_attempts = (user.failed_auth_attempts or 0) + 1
        user.last_failed_auth = datetime.utcnow()
        db.commit()
        logger.warning(
            f"Login failed for {email}: invalid password " f"(attempt {user.failed_auth_attempts})"
        )
        raise invalid_credentials_error

    user.failed_auth_attempts = 0
    user.last_failed_auth = None
    db.commit()

    otp = generate_otp()
    try:
        await store_otp(email, otp)
    except Exception as e:
        logger.exception(f"Failed to store OTP for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification service temporarily unavailable. Please try again.",
        )

    try:
        email_sent = await send_otp_email(email, otp, user.name)
    except Exception as e:
        logger.exception(f"Unexpected email send failure for {email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service temporarily unavailable. Please try again.",
        )

    if not email_sent:
        logger.error(f"Failed to send OTP email after login for {email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification code. Please try again.",
        )

    return {"message": "Verification code sent to your email."}


@router.post("/register")
async def register(
    register_request: RegisterRequest,
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Register a user with email/password and send OTP verification email.

    This endpoint is production-safe and does not rely on dev-only helpers.
    """
    existing_user = db.query(User).filter(User.email == register_request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered. Please sign in.",
        )

    name = register_request.name or register_request.email.split("@")[0]
    user = User(
        email=register_request.email,
        name=name,
        password_hash=hash_password(register_request.password),
        role=Role.CUSTOMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    otp = generate_otp()
    await store_otp(register_request.email, otp)
    email_sent = await send_otp_email(register_request.email, otp, user.name)

    if not email_sent:
        logger.error(f"Failed to send OTP email to {register_request.email} after registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Account created, but failed to send verification code. Please resend OTP.",
        )

    return {"message": "Account created. Verification code sent to your email."}


# ============================================================================
# DEV-ONLY: ENSURE TEST USER
# ============================================================================


@router.post("/dev/ensure-user")
async def dev_ensure_user(
    body: DevEnsureUserRequest,
    db: Session = Depends(get_db),
):
    """
    Create a test user if they don't exist.
    Only available when ENVIRONMENT=development.
    """
    if settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user = db.query(User).filter(User.email == body.email).first()

    if user:
        logger.info(f"Dev: User already exists: {body.email}")
        if body.name and body.name != user.name:
            user.name = body.name
        if body.role and body.role != user.role:
            user.role = body.role
        if db.is_modified(user):
            db.commit()
            db.refresh(user)
        return {
            "created": False,
            "email": body.email,
            "message": "User already exists",
            "role": user.role,
        }

    name = body.name or body.email.split("@")[0]
    role = body.role or Role.CUSTOMER
    user = User(email=body.email, name=name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Dev: User created: {body.email}")

    return {
        "created": True,
        "email": body.email,
        "name": name,
        "role": user.role,
        "message": "User created",
    }


# ============================================================================
# TOKEN REFRESH - WITH TOKEN ROTATION + REUSE DETECTION
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
    - Token reuse detection (if old token used twice â†’ revoke ALL sessions)
    - Token blacklisting to prevent replay attacks
    """
    try:
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

        # TOKEN REUSE DETECTION
        if await is_token_blacklisted(token_jti):
            logger.critical(
                f"SECURITY ALERT: Refresh token reuse detected for user {user_id}",
                extra={
                    "user_id": user_id,
                    "token_jti": token_jti,
                    "ip": request.client.host if request.client else "unknown",
                    "security_event": "token_reuse",
                },
            )

            revoked_count = await delete_all_user_sessions(user_id)
            (
                db.query(UserSession)
                .filter(UserSession.user_id == user_id, UserSession.is_active.is_(True))
                .update({"is_active": False})
            )
            db.commit()

            logger.warning(
                f"Revoked {revoked_count} Redis sessions + DB sessions "
                f"for user {user_id} due to token reuse"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token reuse detected. "
                "All sessions have been revoked. Please sign in again.",
            )

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.error(f"User not found during token refresh: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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
            logger.warning(
                f"Refresh token not found in database for user {user.email}. Possible token reuse."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Generate NEW tokens (rotation)
        new_access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        new_payload = decode_refresh_token(new_refresh_token)
        new_token_jti = new_payload.get("jti") if new_payload else None

        # Blacklist OLD refresh token
        if exp_timestamp:
            remaining_seconds = exp_timestamp - datetime.utcnow().timestamp()
            if remaining_seconds > 0:
                await blacklist_token(token_jti, int(remaining_seconds))

        await delete_refresh_token(token_jti)

        if new_token_jti:
            await store_refresh_token(
                token_jti=new_token_jti,
                user_id=str(user.id),
                device_info={
                    "ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                },
            )

            session_id = str(uuid.uuid4())
            await create_session(
                user_id=str(user.id),
                session_id=session_id,
                token_jti=new_token_jti,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
            )

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


@router.get(
    "/sessions",
    response_model=SessionsResponse,
    summary="Get active sessions",
    description="Retrieve all active sessions for the current user with detailed metadata",
    responses={
        200: {"description": "List of active sessions"},
        401: {"description": "Not authenticated"},
    },
)
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all active sessions for the current user.

    Returns sessions sorted by last_active (most recent first).
    The current session is marked with is_current=True.
    """
    sessions = await get_user_sessions(str(current_user.id))

    current_ip = request.client.host if request.client else "unknown"
    current_ua = request.headers.get("user-agent", "")
    current_jti = getattr(request.state, "token_jti", None)

    session_list = []
    for session in sessions:
        location = None
        location_data = session.get("location")
        if location_data:
            location = SessionLocation(**location_data)

        is_current = False
        if current_jti and session.get("token_jti") == current_jti:
            is_current = True
        elif not current_jti:
            is_current = (
                session.get("ip_address") == current_ip and session.get("user_agent") == current_ua
            )

        session_list.append(
            SessionInfo(
                session_id=session.get("session_id"),
                ip_address=session.get("ip_address", "Unknown"),
                device_type=session.get("device_type", "Unknown"),
                device_name=session.get("device_name", "Unknown Device"),
                browser=session.get("browser", "Unknown"),
                os=session.get("os", "Unknown"),
                location=location,
                created_at=session.get("created_at", datetime.utcnow().isoformat()),
                last_active=session.get("last_active", datetime.utcnow().isoformat()),
                is_current=is_current,
            )
        )

    session_list.sort(key=lambda s: s.last_active, reverse=True)

    logger.info(
        f"User {current_user.email} viewed active sessions",
        extra={"user_id": str(current_user.id), "session_count": len(session_list)},
    )

    return SessionsResponse(
        sessions=session_list,
        total=len(session_list),
        limit=getattr(settings, "MAX_SESSIONS_PER_USER", 5),
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=SessionRevokeResponse,
    summary="Revoke specific session",
    description="Terminate a specific session and invalidate its tokens",
    responses={
        200: {"description": "Session revoked successfully"},
        404: {"description": "Session not found"},
        403: {"description": "Not authorized to revoke this session"},
        401: {"description": "Not authenticated"},
    },
)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Revoke a specific session.

    When a session is revoked:
    1. Session is deleted from Redis
    2. Associated refresh token is blacklisted
    3. Database session is deactivated
    4. User is forced to re-authenticate on that device

    Common use cases:
    - Lost or stolen device
    - Suspicious activity detected
    - Logged in on public computer
    """
    # Verify ownership via Redis sessions
    sessions = await get_user_sessions(str(current_user.id))

    session = next(
        (s for s in sessions if s.get("session_id") == session_id),
        None,
    )

    if not session:
        logger.warning(
            f"User {current_user.email} attempted to revoke non-existent session {session_id}",
            extra={"user_id": str(current_user.id), "session_id": session_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already expired",
        )

    # Delete from Redis
    await delete_session(str(current_user.id), session_id)

    # Blacklist associated refresh token
    token_jti = session.get("token_jti")
    if token_jti:
        await blacklist_token(token_jti, 30 * 24 * 60 * 60)  # max 30 days
        logger.info(f"Blacklisted refresh token {token_jti} for revoked session")

    # Deactivate database session
    db_session = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.id == session_id,
        )
        .first()
    )
    if db_session:
        db_session.is_active = False
        db.commit()

    logger.info(
        f"Session {session_id} revoked by user {current_user.email}",
        extra={
            "user_id": str(current_user.id),
            "session_id": session_id,
            "device_type": session.get("device_type"),
            "ip_address": session.get("ip_address"),
        },
    )

    return SessionRevokeResponse(
        message="Session revoked successfully",
        session_id=session_id,
    )


@router.delete(
    "/sessions",
    response_model=AllSessionsRevokeResponse,
    summary="Revoke all sessions",
    description="Terminate ALL sessions for the current user (including current session)",
    responses={
        200: {"description": "All sessions revoked successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def revoke_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Revoke ALL sessions for the current user.

    âš ï¸ WARNING: Logs the user out from ALL devices including this one.

    Actions performed:
    1. Blacklist all associated refresh tokens
    2. Delete all Redis sessions
    3. Deactivate all database sessions

    Common use cases:
    - Suspected account compromise
    - Force re-auth everywhere after password change
    """
    sessions = await get_user_sessions(str(current_user.id))

    # Blacklist all refresh tokens
    blacklisted_count = 0
    for session in sessions:
        token_jti = session.get("token_jti")
        if token_jti:
            await blacklist_token(token_jti, 30 * 24 * 60 * 60)  # max 30 days
            blacklisted_count += 1

    # Delete all Redis sessions
    deleted_count = await delete_all_user_sessions(str(current_user.id))

    # Deactivate all database sessions
    db_sessions_updated = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_active.is_(True))
        .update({"is_active": False}, synchronize_session=False)
    )
    db.commit()

    logger.warning(
        f"ALL SESSIONS REVOKED for user {current_user.email}. "
        f"Redis sessions deleted: {deleted_count}, "
        f"Tokens blacklisted: {blacklisted_count}, "
        f"DB sessions revoked: {db_sessions_updated}",
        extra={
            "user_id": str(current_user.id),
            "sessions_revoked": deleted_count,
            "tokens_blacklisted": blacklisted_count,
            "db_sessions_revoked": db_sessions_updated,
            "security_event": "all_sessions_revoked",
        },
    )

    # Optional: await send_security_alert_email(current_user.email, ...)

    return AllSessionsRevokeResponse(
        message="All sessions revoked successfully",
        sessions_revoked=deleted_count,
        note="You will be logged out from all devices including this one",
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Logout user and blacklist tokens.

    Actions:
    1. Blacklist current access token
    2. Delete all Redis sessions
    3. Revoke all database sessions
    """
    token_jti = getattr(request.state, "token_jti", None)

    logger.info(f"Logout requested for user {current_user.id} (JTI: {token_jti})")

    if token_jti:
        await blacklist_token(token_jti, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        logger.info(
            f"Access token blacklisted for user {current_user.email}",
            extra={"user_id": str(current_user.id), "token_jti": token_jti},
        )

    deleted_redis_sessions = await delete_all_user_sessions(str(current_user.id))

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

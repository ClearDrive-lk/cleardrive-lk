# backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    # App
    PROJECT_NAME: str = "ClearDrive.lk API"
    VERSION: str = "2.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str | None = None
    DATABASE_SSL_MODE: str = "disable"

    # Redis
    REDIS_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Encryption
    ENCRYPTION_KEY: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # PayHere
    PAYHERE_MERCHANT_ID: str
    PAYHERE_MERCHANT_SECRET: str
    PAYHERE_SANDBOX: bool = True

    # Claude API
    ANTHROPIC_API_KEY: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Email (SMTP)
    SMTP_HOST: str
    SMTP_PORT: int | None = None
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str = "noreply@cleardrive.lk"
    SMTP_FROM_NAME: str = "ClearDrive.lk"
    SMTP_TIMEOUT_SECONDS: float = 10.0
    RESEND_API_KEY: str | None = None

    # OTP
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RATE_LIMIT_REQUESTS: int = 3
    OTP_RATE_LIMIT_WINDOW_MINUTES: int = 5

    # Sentry
    SENTRY_DSN: str | None = None

    # Admin
    ADMIN_EMAILS: str  # Comma-separated

    # Session Management
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_TTL_DAYS: int = 30
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24

    # GeoIP (optional)
    GEOIP_ENABLED: bool = False
    GEOIP_API_KEY: str | None = None
    # RBAC settings
    RBAC_ENABLED: bool = True
    RBAC_STRICT_MODE: bool = True

    # Security
    CLOUDFLARE_API_KEY: str | None = None
    SECURITY_EVENT_RETENTION_DAYS: int = 30
    MAX_FAILED_AUTH_ATTEMPTS: int = 5
    TOKEN_REUSE_DETECTION_ENABLED: bool = True
    SUSPICIOUS_ACTIVITY_THRESHOLD: int = 3

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # Next.js dev
        "http://localhost:19006",  # Expo dev
    ]
    BACKEND_CORS_ORIGIN_REGEX: str | None = None
    BACKEND_ALLOWED_HOSTS: list[str] = [
        "localhost",
        "127.0.0.1",
        "api.cleardrive.lk",
        "*.cleardrive.lk",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

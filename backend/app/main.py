import logging
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.core.rate_limit_middleware import RateLimitMiddleware
from app.modules.admin.audit_routes import router as admin_audit_router
from app.modules.admin.dashboard import router as admin_dashboard_router
from app.modules.gdpr.routes import router as gdpr_router
from app.modules.kyc.admin_routes import router as admin_kyc_router
from app.modules.kyc.routes import router as kyc_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

# Import security middleware
try:
    from app.middleware.security_headers import SecurityHeadersMiddleware

    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False
    logging.warning("Security headers middleware not available")

# Import Redis helpers for initialization
try:
    from app.core.redis_client import close_redis, get_redis, init_redis

    REDIS_INIT_AVAILABLE = True
except ImportError:
    REDIS_INIT_AVAILABLE = False
    init_redis = None  # type: ignore
    close_redis = None  # type: ignore
    get_redis = None  # type: ignore


# Import routers
from app.modules.admin.routes import router as admin_router
from app.modules.auth.routes import router as auth_router
from app.modules.calculator.routes import router as calculator_router
from app.modules.chat.routes import router as chat_router
from app.modules.gazette.routes import router as gazette_router
from app.modules.orders.routes import router as orders_router
from app.modules.payments.routes import router as payments_router
from app.modules.security.routes import router as security_router
from app.modules.shipping.admin_routes import router as shipping_admin_router
from app.modules.shipping.routes import router as shipping_router
from app.modules.test.routes import router as test_router
from app.modules.vehicles.routes import router as vehicles_router
from app.modules.notifications.routes import router as notifications_router
from app.services.scraper.scheduler import scraper_scheduler
from app.services.email_scheduler import email_scheduler
from app.modules.finance.lc_routes import router as lc_router
from app.modules.finance.finance_routes import router as finance_router
from app.modules.finance.insurance_routes import router as insurance_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    Handles:
    - Redis connection initialization
    - Graceful shutdown of services
    """
    logger.info("Starting ClearDrive.lk API...")

    if REDIS_INIT_AVAILABLE and init_redis is not None:
        try:
            await init_redis()
            logger.info("Redis connection initialized")
        except Exception as e:
            logger.warning(f"Redis init_redis() failed: {e}")

    if get_redis is not None:
        try:
            redis = await get_redis()
            await redis.ping()
            logger.info("Redis connected and responsive")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")

    try:
        scraper_scheduler.start()
    except Exception as e:
        logger.warning(f"CD-23 scheduler failed to start: {e}")

    try:
        email_scheduler.start()
    except Exception as e:
        logger.warning(f"CD-120 email scheduler failed to start: {e}")

    yield

    logger.info("Shutting down ClearDrive.lk API...")

    if REDIS_INIT_AVAILABLE and close_redis is not None:
        try:
            await close_redis()
            logger.info("Redis connection closed (using redis_client)")
        except Exception as e:
            logger.warning(f"Error while closing Redis (close_redis): {e}")

    try:
        scraper_scheduler.stop()
    except Exception as e:
        logger.warning(f"CD-23 scheduler failed to stop cleanly: {e}")

    try:
        email_scheduler.stop()
    except Exception as e:
        logger.warning(f"CD-120 email scheduler failed to stop cleanly: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# 1. Trusted Host Middleware (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.BACKEND_ALLOWED_HOSTS)
    logger.info(f"Trusted Host Middleware enabled (production): {settings.BACKEND_ALLOWED_HOSTS}")

# 2. Security Headers Middleware
if SECURITY_MIDDLEWARE_AVAILABLE:
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security Headers Middleware enabled")
else:
    logger.warning("Security Headers Middleware not available")

# 4. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
)
logger.info(
    "CORS enabled for origins: "
    f"{settings.BACKEND_CORS_ORIGINS}, "
    f"regex: {settings.BACKEND_CORS_ORIGIN_REGEX or 'none'}"
)

# 3. Rate Limit Middleware
# Added AFTER CORS to make it the "outer" middleware. This can prevent
# request body consumption issues that sometimes lead to 400 errors in endpoints.
app.add_middleware(RateLimitMiddleware)
logger.info("Rate Limit Middleware enabled")

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(vehicles_router, prefix=settings.API_V1_PREFIX)
app.include_router(calculator_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_audit_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_dashboard_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_kyc_router, prefix=settings.API_V1_PREFIX)
app.include_router(test_router, prefix=settings.API_V1_PREFIX)
app.include_router(kyc_router, prefix=settings.API_V1_PREFIX)
app.include_router(gdpr_router, prefix=settings.API_V1_PREFIX)
app.include_router(gazette_router, prefix=settings.API_V1_PREFIX)
app.include_router(lc_router, prefix=settings.API_V1_PREFIX)
app.include_router(finance_router, prefix=settings.API_V1_PREFIX)
app.include_router(insurance_router, prefix=settings.API_V1_PREFIX)
app.include_router(shipping_admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(shipping_router, prefix=settings.API_V1_PREFIX)
app.include_router(security_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
logger.info(
    "Routers registered: /auth, /vehicles, /calculate, /chat, /orders, /admin, "
    "/shipping, /admin, "
    "/admin/dashboard, /admin/audit-logs, /admin/shipping, /admin/kyc, "
    "/security, /test, /kyc, /gdpr, /gazette, /lc, /finance, /insurance, /notifications"
)

# Serve local runtime data files (e.g., scraped vehicle images).
data_dir = Path(__file__).resolve().parents[1] / "data"
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")
    logger.info("Static data mounted at /data from %s", data_dir)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "ClearDrive.lk API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "security": "enabled" if SECURITY_MIDDLEWARE_AVAILABLE else "basic",
        "endpoints": {
            "auth": f"{settings.API_V1_PREFIX}/auth",
            "vehicles": f"{settings.API_V1_PREFIX}/vehicles",
            "calculator": f"{settings.API_V1_PREFIX}/calculate",
            "payments": f"{settings.API_V1_PREFIX}/payments",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Checks:
    - API responsiveness
    - Redis connection
    - Environment configuration
    """
    redis_status = "unknown"
    if get_redis is not None:
        try:
            redis = await get_redis()
            await redis.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
            logger.warning(f"Redis health check failed: {e}")
    else:
        redis_status = "disabled"

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "security_headers": "enabled" if SECURITY_MIDDLEWARE_AVAILABLE else "disabled",
        "services": {
            "api": "healthy",
            "redis": redis_status,
        },
    }


@app.get("/api/v1/health")
async def health_check_v1():
    return await health_check()


if __name__ == "__main__":
    import os

    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")  # nosec B104

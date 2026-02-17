# backend/app/main.py

import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.redis_client import close_redis, get_redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import security middleware
try:
    from app.middleware.security_headers import SecurityHeadersMiddleware

    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False
    logging.warning("Security headers middleware not available")

# Import Redis helpers for initialization
try:
    from app.core.redis_client import close_redis as redis_close
    from app.core.redis_client import init_redis

    REDIS_INIT_AVAILABLE = True
except ImportError:
    REDIS_INIT_AVAILABLE = False
    init_redis = None  # type: ignore
    redis_close = None  # type: ignore

# Import routers
from app.modules.auth.routes import router as auth_router
from app.modules.orders.routes import router as orders_router
from app.modules.test.routes import router as test_router
from app.modules.vehicles.routes import router as vehicles_router
from app.modules.gdpr.routes import router as gdpr_router

# Configure logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    Handles:
    - Redis connection initialization
    - Graceful shutdown of services
    """
<<<<<<< HEAD
    logger.info("Starting ClearDrive.lk API...")
=======
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("🚀 Starting ClearDrive.lk API...")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    # Initialize Redis (best-effort; don't crash app/tests if Redis is down)
    if REDIS_INIT_AVAILABLE and init_redis is not None:
        try:
            await init_redis()
<<<<<<< HEAD
            logger.info("Redis connection initialized (using init_redis)")
        except Exception as e:
            logger.warning(f"Redis init_redis() failed: {e}")
=======
            logger.info("✅ Redis connection initialized (using init_redis)")
        except Exception as e:
            logger.warning(f"⚠️ Redis init_redis() failed: {e}")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    # Fallback: Try to ping Redis using redis_client
    try:
        redis = await get_redis()
        await redis.ping()
<<<<<<< HEAD
        logger.info("Redis connected and responsive")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")

    yield

    logger.info("Shutting down ClearDrive.lk API...")
=======
        logger.info("✅ Redis connected and responsive")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("👋 Shutting down ClearDrive.lk API...")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    # Close Redis connection (try both methods)
    if REDIS_INIT_AVAILABLE and redis_close is not None:
        try:
            await redis_close()
<<<<<<< HEAD
            logger.info("Redis connection closed (using close_redis)")
        except Exception as e:
            logger.warning(f"Error while closing Redis (close_redis): {e}")
=======
            logger.info("✅ Redis connection closed (using close_redis)")
        except Exception as e:
            logger.warning(f"⚠️ Error while closing Redis (close_redis): {e}")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

    # Fallback: close using redis_client
    try:
        await close_redis()
<<<<<<< HEAD
        logger.info("Redis connection closed (using redis_client)")
    except Exception as e:
        logger.warning(f"Error while closing Redis (redis_client): {e}")


=======
        logger.info("✅ Redis connection closed (using redis_client)")
    except Exception as e:
        logger.warning(f"⚠️ Error while closing Redis (redis_client): {e}")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)


<<<<<<< HEAD
# 1. Trusted Host Middleware (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.BACKEND_ALLOWED_HOSTS)
    logger.info(f"Trusted Host Middleware enabled (production): {settings.BACKEND_ALLOWED_HOSTS}")
=======
# ============================================================================
# SECURITY MIDDLEWARE (Order matters!)
# ============================================================================

# 1. Trusted Host Middleware (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["api.cleardrive.lk", "*.cleardrive.lk"]
    )
    logger.info("✅ Trusted Host Middleware enabled (production)")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

# 2. Security Headers Middleware
if SECURITY_MIDDLEWARE_AVAILABLE:
    app.add_middleware(SecurityHeadersMiddleware)
<<<<<<< HEAD
    logger.info("Security Headers Middleware enabled")
else:
    logger.warning("Security Headers Middleware not available")
=======
    logger.info("✅ Security Headers Middleware enabled")
else:
    logger.warning("⚠️ Security Headers Middleware not available")
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
<<<<<<< HEAD
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX,
=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
)
<<<<<<< HEAD
logger.info(
    "CORS enabled for origins: "
    f"{settings.BACKEND_CORS_ORIGINS}, "
    f"regex: {settings.BACKEND_CORS_ORIGIN_REGEX or 'none'}"
)


=======
logger.info(f"✅ CORS enabled for origins: {settings.BACKEND_CORS_ORIGINS}")


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(vehicles_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(test_router, prefix="/api/v1")
<<<<<<< HEAD
logger.info("Routers registered: /auth, /vehicles, /test")
app.include_router(gdpr_router, prefix=settings.API_V1_PREFIX)
=======
logger.info("✅ Routers registered: /auth, /vehicles, /test")


# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7


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
<<<<<<< HEAD
=======

    # Test Redis connection
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    redis_status = "unknown"
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
        logger.warning(f"Redis health check failed: {e}")

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


<<<<<<< HEAD
@app.get("/api/v1/health")
async def health_check_v1():
    return await health_check()
=======
# ============================================================================
# LEGACY EVENT HANDLERS (Deprecated in favor of lifespan)
# ============================================================================
# Note: These are kept for backward compatibility but lifespan is preferred
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7


@app.on_event("startup")
async def startup_event():
    """
    DEPRECATED: Use lifespan context manager instead.
    Kept for backward compatibility.
    """
    logger.info("Legacy startup event triggered (use lifespan instead)")

<<<<<<< HEAD
=======
    # Initialize Redis using helper if available
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    if REDIS_INIT_AVAILABLE and init_redis is not None:
        try:
            await init_redis()
            logger.info("Redis connection initialized (legacy event)")
        except Exception as e:
            logger.warning(f"Redis initialization failed (legacy event): {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    DEPRECATED: Use lifespan context manager instead.
    Kept for backward compatibility.
    """
    logger.info("Legacy shutdown event triggered (use lifespan instead)")

<<<<<<< HEAD
=======
    # Close Redis using helper if available
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    if REDIS_INIT_AVAILABLE and redis_close is not None:
        try:
            await redis_close()
            logger.info("Redis connection closed (legacy event)")
        except Exception as e:
            logger.warning(f"Error closing Redis (legacy event): {e}")


<<<<<<< HEAD
=======
# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
if __name__ == "__main__":
    import os

    import uvicorn

<<<<<<< HEAD
=======
    # Default to localhost for safety; container platforms can set HOST=0.0.0.0
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(app, host=host, port=port, log_level="info")  # nosec B104
<<<<<<< HEAD
# backend/app/main.py
=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

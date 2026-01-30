# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.redis_client import get_redis, close_redis
from app.middleware.security_headers import SecurityHeadersMiddleware  # 👈 NEW

# Import routers
from app.modules.auth.routes import router as auth_router
from app.modules.vehicles.routes import router as vehicles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("🚀 Starting ClearDrive.lk API...")

    # Initialize Redis (best-effort; don't crash app/tests if Redis is down)
    try:
        redis = await get_redis()
        await redis.ping()
        print("✅ Redis connected")
    except Exception as e:  # pragma: no cover - defensive logging
        print(f"⚠️ Redis not available: {e}")

    yield

    # Shutdown
    print("👋 Shutting down ClearDrive.lk API...")
    try:
        await close_redis()
        print("✅ Redis connection closed")
    except Exception as e:  # pragma: no cover - defensive logging
        print(f"⚠️ Error while closing Redis: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# ============================================================================
# SECURITY MIDDLEWARE (Order matters!)
# ============================================================================

# 1. Trusted Host Middleware (prevent host header attacks)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["api.cleardrive.lk", "*.cleardrive.lk"]
    )

# 2. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)  # 👈 NEW

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(vehicles_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ClearDrive.lk API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "security": "enabled",
        "endpoints": {
            "auth": f"{settings.API_V1_PREFIX}/auth",
            "vehicles": f"{settings.API_V1_PREFIX}/vehicles",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""

    # Test Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "security_headers": "enabled",
        "services": {
            "redis": redis_status,
        },
    }


if __name__ == "__main__":
    import uvicorn
    import os

    # Default to localhost for safety; container platforms can set HOST=0.0.0.0
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)  # nosec B104

"""
Global tiered rate-limit middleware.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from types import SimpleNamespace
from typing import Callable, cast

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import (
    RateLimitUser,
    UserTier,
    apply_rate_limit_headers,
    check_rate_limit,
    get_endpoint_type,
    get_rate_limit,
)
from app.core.redis import is_token_blacklisted
from app.core.security import decode_access_token
from app.modules.auth.models import User
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply tiered rate limits to API requests before route handlers execute."""

    SKIP_PREFIXES = (
        "/",
        "/health",
        "/api/v1/health",
        "/api/v1/docs",
        "/api/v1/redoc",
        "/api/v1/openapi.json",
    )

    SKIP_EXACT = {
        "/api/v1/payments/webhook",
    }

    async def dispatch(self, request: Request, call_next):
        if settings.ENVIRONMENT not in ("production", "test"):
            return await call_next(request)

        path = request.url.path
        if path.startswith("/api/v1/chat/"):
            return await call_next(request)
        if path in self.SKIP_EXACT or path in self.SKIP_PREFIXES:
            return await call_next(request)
        if any(path.startswith(prefix) for prefix in self.SKIP_PREFIXES[2:]):
            return await call_next(request)

        endpoint_type = get_endpoint_type(path)
        default_limits = get_rate_limit(UserTier.STANDARD, endpoint_type)
        default_context = {
            "tier": UserTier.STANDARD.value,
            "minute_limit": default_limits["minute"],
            "minute_remaining": default_limits["minute"],
            "hour_limit": default_limits["hour"],
            "hour_remaining": default_limits["hour"],
        }
        request.state.rate_limit_context = default_context

        db_generator: Generator[Session, None, None] | None = None
        db: Session | None = None

        try:
            if self._has_bearer_token(request):
                db_generator = self._get_db_generator(request)
                db = next(db_generator)
            user = await self._resolve_token(request, db)
            await check_rate_limit(request, user, endpoint_type, db=db)
            context = getattr(request.state, "rate_limit_context", default_context)
            response = await call_next(request)
            self._apply_headers(response, request, context)
            return response
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers or {},
            )
        except Exception as exc:
            logger.exception("Rate limit middleware failed open for %s: %s", path, exc)
            response = await call_next(request)
            context = getattr(request.state, "rate_limit_context", default_context)
            self._apply_headers(response, request, context)
            return response
        finally:
            if db_generator is not None:
                self._close_db_generator(db_generator)

    def _has_bearer_token(self, request: Request) -> bool:
        auth_header = request.headers.get("Authorization")
        return bool(auth_header and auth_header.startswith("Bearer "))

    async def _resolve_token(self, request: Request, db: Session | None) -> RateLimitUser | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if payload is None:
            return None

        token_jti = payload.get("jti")
        if token_jti and await is_token_blacklisted(str(token_jti)):
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        if db is None:
            return SimpleNamespace(id=user_id)

        user = db.query(User).filter(User.id == user_id).first()
        if user is not None:
            return user

        return SimpleNamespace(id=user_id)

    def _get_db_generator(self, request: Request) -> Generator[Session, None, None]:
        db_dependency = cast(
            Callable[[], Generator[Session, None, None]],
            request.app.dependency_overrides.get(get_db, get_db),
        )
        return cast(Generator[Session, None, None], db_dependency())

    def _close_db_generator(self, generator: Generator[Session, None, None]) -> None:
        try:
            next(generator)
        except StopIteration:
            return

    def _apply_headers(self, response, request: Request, context: dict[str, object]) -> None:
        request.state.rate_limit_context = context
        apply_rate_limit_headers(response, request)

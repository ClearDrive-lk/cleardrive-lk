# backend/tests/conftest.py
"""
Pytest configuration and fixtures.
"""

import os

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-min-32-characters-long")
os.environ.setdefault("ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("PAYHERE_MERCHANT_ID", "test-merchant-id")
os.environ.setdefault("PAYHERE_MERCHANT_SECRET", "test-merchant-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SMTP_HOST", "smtp.gmail.com")
os.environ.setdefault("SMTP_USERNAME", "test@gmail.com")
os.environ.setdefault("SMTP_PASSWORD", "test-password")
os.environ.setdefault("ADMIN_EMAILS", "admin@cleardrive.lk")
os.environ.setdefault("ENVIRONMENT", "test")

import asyncio  # noqa: E402
from typing import AsyncGenerator, Generator  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

import pytest  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.core.redis_client import get_redis  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.auth.models import Role, User  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from httpx import AsyncClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# Test database (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================================================
# EVENT LOOP FIXTURE
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.

    This prevents "Event loop is closed" errors when using async fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create test database for each test function.

    Yields:
        SQLAlchemy Session
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================================
# CLIENT FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create synchronous test client.

    Use this for non-async tests.

    Args:
        db: Database session fixture

    Yields:
        TestClient
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db: Session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create asynchronous test client.

    Use this for async tests that need to call Redis or other async services.

    Args:
        db: Database session fixture

    Yields:
        AsyncClient
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================================
# REDIS FIXTURES
# ============================================================================


@pytest.fixture(scope="function")
async def redis_client():
    """
    Get Redis client for tests.

    Yields:
        Redis client
    """
    try:
        client = await get_redis()
        yield client
    except Exception as e:
        # If Redis is not available, skip tests that require it
        pytest.skip(f"Redis not available: {e}")


# ============================================================================
# USER FIXTURES
# ============================================================================


@pytest.fixture
def test_user(db: Session):
    """
    Create a test user.

    Args:
        db: Database session

    Returns:
        User object
    """
    user = User(
        email="test@example.com",
        name="Test User",
        role=Role.CUSTOMER,
        google_id="test_google_id",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session):
    """
    Create an admin user.

    Args:
        db: Database session

    Returns:
        Admin User object
    """
    user = User(
        email="admin@example.com",
        name="Admin User",
        role=Role.ADMIN,
        google_id="admin_google_id",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# AUTH FIXTURES
# ============================================================================


@pytest.fixture
def auth_headers(test_user):
    """
    Create authentication headers for test user.

    Args:
        test_user: User fixture

    Returns:
        Dict with Authorization header
    """
    access_token = create_access_token(
        data={
            "sub": str(test_user.id),
            "email": test_user.email,
            "role": test_user.role.value,
        }
    )

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(admin_user):
    """
    Create authentication headers for admin user.

    Args:
        admin_user: Admin user fixture

    Returns:
        Dict with Authorization header
    """
    access_token = create_access_token(
        data={
            "sub": str(admin_user.id),
            "email": admin_user.email,
            "role": admin_user.role.value,
        }
    )

    return {"Authorization": f"Bearer {access_token}"}


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "redis: mark test as requiring Redis")
    config.addinivalue_line("markers", "integration: mark test as integration test")


# ============================================================================
# STATEFUL MOCK REDIS FOR TESTS
# ============================================================================


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    """
    Stateful mock Redis for OTP tests.
    """
    store = {}  # In-memory store to simulate Redis

    async def setex(key, expiry, value):
        store[key] = value
        return True

    async def get(key):
        return store.get(key)

    async def delete(*keys):
        count = 0
        for key in keys:
            if store.pop(key, None) is not None:
                count += 1
        return count

    async def incr(key):
        value = store.get(key, "0")
        try:
            value = int(value)
        except ValueError:
            value = 0
        value += 1
        store[key] = str(value)
        return value

    async def expire(key, _expiry):
        # no-op for tests
        return True

    async def ttl(key):
        return 300  # arbitrary positive TTL

    async def exists(key):
        return 1 if key in store else 0

    async def keys(pattern="*"):
        if pattern == "*":
            return list(store.keys())
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return [k for k in store.keys() if k.startswith(prefix)]
        return [k for k in store.keys() if k == pattern]

    mock_client = AsyncMock()
    mock_client.setex.side_effect = setex
    mock_client.get.side_effect = get
    mock_client.delete.side_effect = delete
    mock_client.incr.side_effect = incr
    mock_client.expire.side_effect = expire
    mock_client.ttl.side_effect = ttl
    mock_client.exists.side_effect = exists
    mock_client.keys.side_effect = keys

    mocker.patch("app.core.redis_client.get_redis", return_value=mock_client)
    mocker.patch("app.core.redis.get_redis", return_value=mock_client)
    yield mock_client

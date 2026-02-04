# backend/tests/conftest.py
"""
Pytest configuration and fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from app.core.database import Base, get_db
from app.core.redis_client import get_redis
from app.main import app
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

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
    from app.modules.auth.models import Role, User

    user = User(
        email="test@example.com", name="Test User", role=Role.CUSTOMER, google_id="test_google_id"
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
    from app.modules.auth.models import Role, User

    user = User(
        email="admin@example.com", name="Admin User", role=Role.ADMIN, google_id="admin_google_id"
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
    from app.core.security import create_access_token

    access_token = create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email, "role": test_user.role.value}
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
    from app.core.security import create_access_token

    access_token = create_access_token(
        data={"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role.value}
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

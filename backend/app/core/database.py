# backend/app/core/database.py

from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# Configure engine arguments
engine_kwargs: Dict[str, Any] = {
    "pool_pre_ping": True,  # Verify connections before using
}

# Fix for "postgres://" in DATABASE_URL (SQLAlchemy 1.4+ requires "postgresql://")
db_url = str(settings.DATABASE_URL)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# SQLite does not support pool_size/max_overflow
if "sqlite" not in str(settings.DATABASE_URL):
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

# Create engine
engine = create_engine(
    db_url,
    **engine_kwargs,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create base class for models
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Database session dependency.

    Usage:
        @router.get("/")
        async def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

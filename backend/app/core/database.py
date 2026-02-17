# backend/app/core/database.py

from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# Configure engine arguments
engine_kwargs: Dict[str, Any] = {
    "pool_pre_ping": True,  # Verify connections before using
}

# SQLite does not support pool_size/max_overflow
<<<<<<< HEAD
if "sqlite" not in str(settings.DATABASE_URL):
=======
if "sqlite" not in settings.DATABASE_URL:
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create base class for models
class Base(DeclarativeBase):
    pass


<<<<<<< HEAD
=======
# 👇 THIS LINE IS THE KEY


>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
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

# backend/app/core/database.py

from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings

# Configure engine arguments
engine_kwargs: Dict[str, Any] = {
    "pool_pre_ping": True,  # Verify connections before using
}

# Fix for "postgres://" in DATABASE_URL (SQLAlchemy 1.4+ requires "postgresql://")
db_url = str(settings.DATABASE_URL)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

url = make_url(db_url)
host = (url.host or "").lower()
is_sqlite = url.drivername.startswith("sqlite")
is_supabase = "supabase.co" in host

# Ensure SSL is explicitly enabled for managed Postgres when configured outside the URL.
if not is_sqlite and settings.DATABASE_SSL_MODE.lower() == "require" and "sslmode" not in url.query:
    url = url.update_query_dict({"sslmode": "require"})

# Supabase poolers behave better without a long-lived SQLAlchemy pool inside the app.
if is_supabase:
    engine_kwargs["poolclass"] = NullPool

# SQLite does not support pool_size/max_overflow. NullPool also bypasses them.
elif not is_sqlite:
    engine_kwargs.update(
        {
            "pool_size": 5,
            "max_overflow": 10,
        }
    )

# Create engine
engine = create_engine(
    url,
    use_native_hstore=False,
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

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


def _is_supabase_managed_host(hostname: str) -> bool:
    normalized = hostname.strip().lower()
    if not normalized:
        return False
    return any(
        marker in normalized for marker in ("supabase.co", "supabase.com", "pooler.supabase")
    )


is_supabase = _is_supabase_managed_host(host)

# Avoid psycopg2's hstore on-connect probe against Supabase/pooler connections.
if is_supabase and url.drivername in {"postgresql", "postgresql+psycopg2"}:
    url = url.set(drivername="postgresql+psycopg")

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
create_engine_kwargs = dict(engine_kwargs)
if not is_sqlite:
    create_engine_kwargs["use_native_hstore"] = False

engine = create_engine(
    url,
    **create_engine_kwargs,
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

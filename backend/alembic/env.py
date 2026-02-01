# backend/alembic/env.py
# backend/alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context  # type: ignore
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import Base

# Import ALL models so Alembic can detect them
from app.modules.auth.models import User, Session
from app.modules.vehicles.models import Vehicle
from app.modules.orders.models import Order, OrderStatusHistory
from app.modules.payments.models import Payment, PaymentIdempotency
from app.modules.kyc.models import KYCDocument
from app.modules.shipping.models import ShipmentDetails, ShippingDocument
from app.modules.security.models import (
    FileIntegrity,
    SecurityEvent,
    UserReputation,
    RateLimitViolation,
)
from app.modules.gdpr.models import GDPRRequest

# ... rest of the file stays the same

# Import all models here so Alembic can detect them
# We'll add these as we create models
# from app.modules.auth.models import User
# from app.modules.vehicles.models import Vehicle
# etc...

# this is the Alembic Config object
config = context.config

# Set sqlalchemy.url from our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

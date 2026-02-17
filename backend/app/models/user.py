"""
User model.
"""
<<<<<<< HEAD

=======
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7
import uuid
from datetime import datetime

from app.core.database import Base
from app.core.permissions import Role
from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    google_id = Column(String(255), unique=True, index=True)
    role = Column(Enum(Role), nullable=False, default=Role.CUSTOMER)  # type: ignore
    password_hash = Column(String(255))  # For admin backup password
    phone = Column(String(20))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Security tracking
    failed_auth_attempts = Column(Integer, default=0, nullable=False)
    last_failed_auth = Column(DateTime)

    def __repr__(self):
        return f"<User {self.email}>"

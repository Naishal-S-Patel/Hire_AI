"""
User ORM model — stores registered users with hashed passwords.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class User(Base):
    """users table — registered platform users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False, index=True)
    full_name = Column(Text, nullable=True)
    hashed_password = Column(Text, nullable=True)  # null for Google-only users
    picture = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(Text, default="local")  # local | google
    role = Column(Text, default="USER", nullable=False)  # HR | USER
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<User {self.email}>"

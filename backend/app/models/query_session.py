"""
QuerySession ORM model — logs AI query-assistant interactions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db import Base


class QuerySession(Base):
    """query_sessions table — stores NL query parsing sessions."""

    __tablename__ = "query_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_query = Column(Text, nullable=False)
    parsed_filters = Column(JSONB, default=dict)
    results_count = Column(Text, nullable=True)
    user_id = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<QuerySession {self.raw_query[:40]}>"

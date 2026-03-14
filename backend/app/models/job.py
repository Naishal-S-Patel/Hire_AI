"""
Job ORM model.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Numeric, TIMESTAMP, ARRAY, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db import Base


class Job(Base):
    """jobs table — job descriptions created by recruiters."""

    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False, index=True)
    company = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(ARRAY(Text), default=list)
    required_skills = Column(ARRAY(Text), default=list)
    preferred_skills = Column(ARRAY(Text), default=list)
    location = Column(Text, nullable=True)
    min_experience = Column(Numeric, nullable=True)
    max_experience = Column(Numeric, nullable=True)
    experience_required = Column(Numeric, nullable=True)
    salary_range = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_by_hr = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Job {self.title}>"

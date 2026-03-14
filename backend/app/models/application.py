"""
Application ORM model — links candidates to jobs.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Text, Numeric, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db import Base


class Application(Base):
    """applications table — a candidate's application to a specific job."""

    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=True, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    hr_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Denormalized candidate data for applications without candidate records
    candidate_name = Column(Text, nullable=True)
    candidate_email = Column(Text, nullable=True, index=True)
    candidate_phone = Column(Text, nullable=True)
    resume_file_url = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    experience_years = Column(Numeric, nullable=True)
    skills = Column(ARRAY(Text), default=list)
    education = Column(JSONB, default=list)
    ai_summary = Column(Text, nullable=True)
    risk_score = Column(Numeric, nullable=True)
    
    status = Column(Text, default="PENDING")  # PENDING | SHORTLISTED | ACCEPTED | REJECTED
    ats_score = Column(Numeric, nullable=True)
    source = Column(Text, default="UPLOAD")  # UPLOAD | EMAIL | PORTAL
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Application candidate={self.candidate_id} job={self.job_id}>"

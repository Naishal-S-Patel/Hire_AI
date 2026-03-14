"""
Candidate ORM model.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, Text, TIMESTAMP, ARRAY, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db import Base


class Candidate(Base):
    """candidates table — stores parsed resume data and AI enrichments."""

    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(Text, nullable=False, index=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    phone = Column(Text, nullable=True)
    mobile_number = Column(Text, nullable=True, index=True)
    location = Column(Text, nullable=True)
    place_of_residence = Column(Text, nullable=True)
    confidence_score = Column(Numeric, nullable=True)
    technical_score = Column(Numeric, nullable=True)
    video_screening_completed = Column(String, default='pending')
    experience_years = Column(Numeric, nullable=True)
    skills = Column(ARRAY(Text), default=list)
    education = Column(JSONB, default=list)
    source = Column(Text, nullable=True)
    resume_path = Column(Text, nullable=True)       # original filename
    resume_file_url = Column(Text, nullable=True)   # path to stored file on disk
    resume_text = Column(Text, nullable=True)        # extracted plain text
    resume_hash = Column(Text, nullable=True, index=True)  # SHA-256 of file bytes
    parsed_json = Column(JSONB, default=dict)
    ats_score = Column(Numeric, nullable=True)
    ai_summary = Column(Text, nullable=True)
    fraud_flags = Column(JSONB, default=dict)
    skill_graph_data = Column(JSONB, default=dict)
    canonical_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # ── Candidate Integrity System fields ─────────────────────
    is_duplicate = Column(Boolean, default=False)
    fraud_score = Column(Numeric, nullable=True, default=0)
    fraud_reason = Column(Text, nullable=True)
    application_attempts = Column(Integer, default=1)
    is_flagged = Column(Boolean, default=False)
    verification_status = Column(String(50), default="pending")  # pending, valid, flagged, blocked
    status = Column(String(50), default="applied")  # applied, shortlisted, assessment_sent, hired, rejected

    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Candidate {self.full_name} ({self.email})>"

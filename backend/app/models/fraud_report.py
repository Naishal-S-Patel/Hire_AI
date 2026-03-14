"""
FraudReport ORM model — stores fraud detection results per candidate.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Numeric, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db import Base


class FraudReport(Base):
    """fraud_reports table — AI fraud analysis per candidate."""

    __tablename__ = "fraud_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    risk_score = Column(Numeric, nullable=True)
    flags = Column(JSONB, default=list)
    details = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<FraudReport candidate={self.candidate_id} risk={self.risk_score}>"

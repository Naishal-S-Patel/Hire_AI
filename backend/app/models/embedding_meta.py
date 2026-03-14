"""
EmbeddingMeta ORM model — tracks vectors stored in ChromaDB.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class EmbeddingMeta(Base):
    """embeddings_meta table — metadata for vectors in ChromaDB."""

    __tablename__ = "embeddings_meta"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    chroma_id = Column(Text, nullable=False, unique=True)
    source_text = Column(Text, nullable=True)
    model_name = Column(Text, default="all-MiniLM-L6-v2")
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<EmbeddingMeta candidate={self.candidate_id}>"

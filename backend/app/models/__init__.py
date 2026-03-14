"""
Models package — re-exports all ORM models for convenient access.
"""

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application
from app.models.embedding_meta import EmbeddingMeta
from app.models.fraud_report import FraudReport
from app.models.query_session import QuerySession
from app.models.user import User

__all__ = [
    "Candidate",
    "Job",
    "Application",
    "EmbeddingMeta",
    "FraudReport",
    "QuerySession",
    "User",
]


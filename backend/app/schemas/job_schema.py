"""
Pydantic schemas for Job endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Create a new job description."""
    title: str
    company: Optional[str] = None
    description: str
    requirements: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    salary_range: dict[str, Any] = Field(default_factory=dict)


class JobOut(BaseModel):
    """Job read-model."""
    id: uuid.UUID
    title: str
    company: Optional[str] = None
    description: str
    requirements: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    min_experience: Optional[float] = None
    max_experience: Optional[float] = None
    salary_range: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ShortlistRequest(BaseModel):
    """Shortlist candidates for a job."""
    job_id: uuid.UUID
    candidate_ids: list[uuid.UUID]


class ShortlistOut(BaseModel):
    """Shortlist result."""
    job_id: uuid.UUID
    shortlisted: list[uuid.UUID]
    message: str


class InterviewScheduleRequest(BaseModel):
    """Schedule interview for a candidate."""
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    interview_time: datetime
    notes: Optional[str] = None


class InterviewScheduleOut(BaseModel):
    """Interview schedule confirmation."""
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    interview_time: datetime
    status: str = "scheduled"


class CompareRequest(BaseModel):
    """Compare multiple candidates."""
    candidate_ids: list[uuid.UUID]
    job_id: Optional[uuid.UUID] = None


class CompareOut(BaseModel):
    """Comparison result."""
    candidates: list[dict[str, Any]]
    ranking: list[uuid.UUID]

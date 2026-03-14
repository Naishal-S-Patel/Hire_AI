"""
Pydantic schemas for Candidate endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    """Payload when creating a candidate manually."""
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[float] = None
    skills: list[str] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    source: Optional[str] = None


class CandidateUpdate(BaseModel):
    """Partial update payload."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[float] = None
    skills: Optional[list[str]] = None
    education: Optional[list[dict[str, Any]]] = None
    source: Optional[str] = None


class CandidateOut(BaseModel):
    """Read-model returned from the API."""
    id: uuid.UUID
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[float] = None
    skills: list[str] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    source: Optional[str] = None
    resume_path: Optional[str] = None
    resume_file_url: Optional[str] = None
    resume_text: Optional[str] = None
    resume_hash: Optional[str] = None
    parsed_json: dict[str, Any] = Field(default_factory=dict)
    ats_score: Optional[float] = None
    ai_summary: Optional[str] = None
    fraud_flags: dict[str, Any] = Field(default_factory=dict)
    skill_graph_data: dict[str, Any] = Field(default_factory=dict)
    canonical_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CandidateSummaryOut(BaseModel):
    """Three-line AI summary."""
    candidate_id: uuid.UUID
    summary: str


class FraudReportOut(BaseModel):
    """Fraud detection report."""
    candidate_id: uuid.UUID
    risk_score: float
    flags: list[dict[str, Any]] = Field(default_factory=list)
    details: Optional[str] = None


class SkillGraphOut(BaseModel):
    """Radar-chart skill graph data."""
    candidate_id: uuid.UUID
    skill_graph: dict[str, Any] = Field(default_factory=dict)

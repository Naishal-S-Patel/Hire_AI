"""
Pydantic schemas for Search endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    """Semantic vector search request."""
    query: str
    top_k: int = 10
    filters: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A single search result."""
    candidate_id: uuid.UUID
    score: float
    full_name: str
    email: str
    skills: list[str] = Field(default_factory=list)
    experience_years: Optional[float] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    results: list[SearchResult]
    total: int


class QueryAssistantRequest(BaseModel):
    """Natural-language query for the AI assistant."""
    query: str


class QueryAssistantResponse(BaseModel):
    """Structured filter output from the AI assistant."""
    original_query: str
    parsed_filters: dict[str, Any] = Field(default_factory=dict)
    results: list[SearchResult] = Field(default_factory=list)
    total: int = 0


class NormalizeRequest(BaseModel):
    """Normalize a skill / job-title string."""
    text: str
    category: str = "skill"  # skill | title | location


class NormalizeResponse(BaseModel):
    """Normalized output."""
    original: str
    normalized: str
    category: str

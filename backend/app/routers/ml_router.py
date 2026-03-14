"""
ML router — exposes all ML module endpoints under /ml/v1/*.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ml/v1", tags=["ml"])


# ── Request / Response schemas ────────────────────────────


class TextInput(BaseModel):
    text: str


class ResumeParseResult(BaseModel):
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education: list[dict[str, Any]] = Field(default_factory=list)
    raw_length: int = 0


class EmbeddingRequest(BaseModel):
    text: str
    candidate_id: str | None = None


class EmbeddingResult(BaseModel):
    vector: list[float] = Field(default_factory=list)
    dimensions: int = 0
    chroma_id: str | None = None


class ATSRequest(BaseModel):
    resume_text: str
    job_description: str


class ATSResult(BaseModel):
    ats_score: float
    semantic_similarity: float
    keyword_overlap_score: float
    matched_keywords: list[str] = Field(default_factory=list)


class DedupeCheckRequest(BaseModel):
    candidate_id: str
    threshold: float = 0.85


class DedupeCheckResult(BaseModel):
    candidate_id: str
    duplicates: list[dict[str, Any]] = Field(default_factory=list)


class VideoAssessResult(BaseModel):
    transcription: dict[str, Any] = Field(default_factory=dict)
    communication: dict[str, Any] = Field(default_factory=dict)


class SkillGraphInput(BaseModel):
    skills: list[str]


class SkillGraphResult(BaseModel):
    categories: list[str] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class SummaryInput(BaseModel):
    full_name: str
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    location: str | None = None
    education: list[dict[str, str]] = Field(default_factory=list)


class SummaryResult(BaseModel):
    summary: str


class FraudDetectInput(BaseModel):
    resume_text: str
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education: list[dict[str, str]] = Field(default_factory=list)


class FraudDetectResult(BaseModel):
    risk_score: float
    flags: list[dict[str, Any]] = Field(default_factory=list)
    total_flags: int = 0


class QueryParseInput(BaseModel):
    query: str


class QueryParseResult(BaseModel):
    original_query: str
    parsed_filters: dict[str, Any] = Field(default_factory=dict)
    method: str = ""


# ── Endpoints ─────────────────────────────────────────────


@router.post("/skill_extract", response_model=ResumeParseResult, summary="Extract skills from text")
async def skill_extract(body: TextInput):
    """Parse resume text and extract structured information."""
    from app.ml.resume_parser.parser import parse_resume
    return parse_resume(body.text)


@router.post("/embeddings", response_model=EmbeddingResult, summary="Generate embeddings")
async def generate_embeddings(body: EmbeddingRequest):
    """Generate dense vector embedding for text. Optionally stores in ChromaDB."""
    from app.ml.embeddings.embedder import encode_text, upsert_embedding

    vector = encode_text(body.text)
    chroma_id = None

    if body.candidate_id:
        chroma_id = upsert_embedding(body.candidate_id, body.text)

    return EmbeddingResult(vector=vector, dimensions=len(vector), chroma_id=chroma_id)


@router.post("/ats_score", response_model=ATSResult, summary="Compute ATS score")
async def ats_score(body: ATSRequest):
    """Compute ATS compatibility score between resume and JD."""
    from app.ml.ats.ats_score import compute_ats_score
    result = compute_ats_score(body.resume_text, body.job_description)
    return ATSResult(**result)


@router.post("/dedupe_check", response_model=DedupeCheckResult, summary="Check for duplicates")
async def dedupe_check(body: DedupeCheckRequest):
    """Check if a candidate has potential duplicates in the system."""
    from app.ml.dedupe.dedupe_engine import find_duplicates
    dups = find_duplicates(body.candidate_id, threshold=body.threshold)
    return DedupeCheckResult(candidate_id=body.candidate_id, duplicates=dups)


@router.post("/video/assess", response_model=VideoAssessResult, summary="Assess video interview")
async def video_assess(file: UploadFile = File(...)):
    """Upload a video file and assess communication skills."""
    from app.ml.video.video_assessment import assess_video

    suffix = os.path.splitext(file.filename or "video.mp4")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await assess_video(tmp_path)
        return VideoAssessResult(**result)
    finally:
        os.unlink(tmp_path)


@router.post("/skill_graph", response_model=SkillGraphResult, summary="Generate skill graph")
async def skill_graph(body: SkillGraphInput):
    """Generate radar-chart skill graph data from a list of skills."""
    from app.ml.skill_graph.skill_graph import build_skill_graph
    result = build_skill_graph(body.skills)
    return SkillGraphResult(**result)


@router.post("/summary/generate", response_model=SummaryResult, summary="Generate AI summary")
async def generate_summary(body: SummaryInput):
    """Generate a 3-line AI summary for a candidate."""
    from app.ml.summary.summary_generator import generate_summary as gen
    summary = await gen(body.model_dump())
    return SummaryResult(summary=summary)


@router.post("/fraud/detect", response_model=FraudDetectResult, summary="Detect resume fraud")
async def fraud_detect(body: FraudDetectInput):
    """Run fraud detection on resume data."""
    from app.ml.fraud_detection.fraud_detector import run_fraud_detection
    result = run_fraud_detection(
        resume_text=body.resume_text,
        skills=body.skills,
        experience_years=body.experience_years,
        education=body.education,
    )
    return FraudDetectResult(**result)


@router.post("/query/parse", response_model=QueryParseResult, summary="Parse NL query")
async def query_parse(body: QueryParseInput):
    """Convert a natural-language query to structured filters."""
    from app.ml.query_assistant.query_parser import parse_query
    result = await parse_query(body.query)
    return QueryParseResult(**result)

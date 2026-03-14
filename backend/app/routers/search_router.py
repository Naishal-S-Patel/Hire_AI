"""
Search router — semantic search, query assistant, normalize, and candidate comparison.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.candidate import Candidate
from app.schemas.search_schema import (
    NormalizeRequest,
    NormalizeResponse,
    QueryAssistantRequest,
    QueryAssistantResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SearchResult,
)
from app.schemas.job_schema import CompareRequest, CompareOut

router = APIRouter(tags=["search"])


@router.post(
    "/api/v1/search/semantic",
    response_model=SemanticSearchResponse,
    summary="Hybrid semantic search",
)
async def semantic_search(
    body: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Hybrid search: SQL pre-filter → ChromaDB vector search.
    """
    from app.ml.embeddings.embedder import query_similar

    # Step 1: Vector search in ChromaDB
    chroma_results = query_similar(body.query, top_k=body.top_k)

    candidate_ids = [
        r["candidate_id"] for r in chroma_results if r.get("candidate_id")
    ]

    if not candidate_ids:
        return SemanticSearchResponse(results=[], total=0)

    # Step 2: Enrich with SQL data
    uuids = []
    for cid in candidate_ids:
        try:
            uuids.append(uuid.UUID(cid))
        except ValueError:
            continue

    result = await db.execute(select(Candidate).where(Candidate.id.in_(uuids)))
    candidates = {str(c.id): c for c in result.scalars().all()}

    # Build scored results
    results: list[SearchResult] = []
    for cr in chroma_results:
        cid = cr.get("candidate_id")
        if cid and cid in candidates:
            c = candidates[cid]
            results.append(SearchResult(
                candidate_id=c.id,
                score=cr["score"],
                full_name=c.full_name,
                email=c.email,
                skills=c.skills or [],
                experience_years=float(c.experience_years) if c.experience_years else None,
            ))

    # Apply SQL filters if provided
    if body.filters.get("min_experience"):
        min_exp = float(body.filters["min_experience"])
        results = [r for r in results if r.experience_years and r.experience_years >= min_exp]
    if body.filters.get("location"):
        loc = body.filters["location"].lower()
        # Would need location field in SearchResult for full filtering
        pass
    if body.filters.get("skills"):
        required_skills = {s.lower() for s in body.filters["skills"]}
        results = [r for r in results if required_skills.issubset({s.lower() for s in r.skills})]

    return SemanticSearchResponse(results=results, total=len(results))


@router.post(
    "/api/v1/search/query-assistant",
    response_model=QueryAssistantResponse,
    summary="Natural-language query assistant",
)
async def query_assistant(
    body: QueryAssistantRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Convert a natural-language query to structured filters, then search.
    """
    from app.ml.query_assistant.query_parser import parse_query

    parsed = await parse_query(body.query)
    filters = parsed.get("parsed_filters", {})

    # Build SQL query with parsed filters
    stmt = select(Candidate)
    if filters.get("min_experience"):
        stmt = stmt.where(Candidate.experience_years >= filters["min_experience"])
    if filters.get("location"):
        stmt = stmt.where(Candidate.location.ilike(f"%{filters['location']}%"))
    if filters.get("skills"):
        for skill in filters["skills"]:
            stmt = stmt.where(Candidate.skills.contains([skill]))

    stmt = stmt.limit(20)
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    results = [
        SearchResult(
            candidate_id=c.id,
            score=1.0,
            full_name=c.full_name,
            email=c.email,
            skills=c.skills or [],
            experience_years=float(c.experience_years) if c.experience_years else None,
        )
        for c in candidates
    ]

    return QueryAssistantResponse(
        original_query=body.query,
        parsed_filters=filters,
        results=results,
        total=len(results),
    )


@router.post(
    "/api/v1/search/normalize",
    response_model=NormalizeResponse,
    summary="Normalize a skill / title / location string",
)
async def normalize(body: NormalizeRequest):
    """
    Normalize a skill name, job title, or location string.
    """
    normalized = body.text.strip().lower().title()

    # Common normalization mappings
    skill_map = {
        "js": "JavaScript", "ts": "TypeScript", "py": "Python",
        "react.js": "React", "reactjs": "React", "node": "Node.js",
        "k8s": "Kubernetes", "ml": "Machine Learning", "dl": "Deep Learning",
        "pg": "PostgreSQL", "postgres": "PostgreSQL",
    }
    if body.category == "skill":
        text_lower = body.text.strip().lower()
        normalized = skill_map.get(text_lower, normalized)

    return NormalizeResponse(
        original=body.text,
        normalized=normalized,
        category=body.category,
    )


@router.post(
    "/api/v1/compare",
    response_model=CompareOut,
    summary="Compare multiple candidates",
)
async def compare_candidates(
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Compare multiple candidates side-by-side, optionally against a job description.
    """
    result = await db.execute(select(Candidate).where(Candidate.id.in_(body.candidate_ids)))
    candidates = result.scalars().all()

    if not candidates:
        raise HTTPException(status_code=404, detail="No candidates found")

    # Build comparison data
    comparison: list[dict] = []
    for c in candidates:
        entry = {
            "id": str(c.id),
            "full_name": c.full_name,
            "email": c.email,
            "skills": c.skills or [],
            "experience_years": float(c.experience_years) if c.experience_years else 0,
            "ats_score": float(c.ats_score) if c.ats_score else 0,
        }

        # If a job is specified, compute ATS score
        if body.job_id:
            from app.models.job import Job
            job_result = await db.execute(select(Job).where(Job.id == body.job_id))
            job = job_result.scalar_one_or_none()
            if job:
                from app.ml.ats.ats_score import compute_ats_score
                ats = compute_ats_score(
                    " ".join(c.skills or []) + " " + str(c.parsed_json),
                    job.description,
                )
                entry["ats_score"] = ats["ats_score"]

        comparison.append(entry)

    # Rank by ATS score
    comparison.sort(key=lambda x: x.get("ats_score", 0), reverse=True)
    ranking = [uuid.UUID(c["id"]) for c in comparison]

    return CompareOut(candidates=comparison, ranking=ranking)

"""
Candidate router — upload, list, get, patch, summary, fraud-report, skill-graph, analytics.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Header
from fastapi.responses import FileResponse
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.candidate import Candidate
from app.schemas.candidate_schema import (
    CandidateOut,
    CandidateSummaryOut,
    CandidateUpdate,
    FraudReportOut,
    SkillGraphOut,
)

logger = logging.getLogger(__name__)
from app.services.duplicate_detector import check_duplicate_candidate
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])

# Ensure uploads directory exists at startup
_UPLOADS_DIR = Path(settings.UPLOADS_DIR)
_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ── STATIC ROUTES (must be before /{candidate_id} wildcard) ──────────────────

class BasicDetailsCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile_number: str
    place_of_residence: str


@router.post("/basic-details", summary="Submit candidate basic details")
async def submit_basic_details(
    details: BasicDetailsCreate,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None),
):
    """Submit candidate basic details with duplicate detection."""
    # Auth is optional — candidates can submit without a recruiter token
    # but if a token is provided, validate it (don't block on missing token)
    duplicate_check = await check_duplicate_candidate(
        email=details.email,
        mobile_number=details.mobile_number,
        db=db,
    )
    if duplicate_check["is_duplicate"]:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Duplicate candidate detected (same {duplicate_check['match_type']})",
                "match_type": duplicate_check["match_type"],
                "existing_id": duplicate_check["existing_candidate_id"],
            },
        )
    candidate = Candidate(
        first_name=details.first_name,
        last_name=details.last_name,
        full_name=f"{details.first_name} {details.last_name}",
        email=details.email,
        mobile_number=details.mobile_number,
        place_of_residence=details.place_of_residence,
        source="portal",
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    return {
        "id": str(candidate.id),
        "first_name": candidate.first_name,
        "last_name": candidate.last_name,
        "email": candidate.email,
        "mobile_number": candidate.mobile_number,
        "place_of_residence": candidate.place_of_residence,
        "created_at": candidate.created_at,
    }
@router.post("/upload", response_model=CandidateOut, status_code=201, summary="Upload & parse a resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()

    # ── 1. Hash the file for duplicate detection ───────────
    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate by hash OR email (after parsing)
    hash_check = await db.execute(select(Candidate).where(Candidate.resume_hash == file_hash))
    if hash_check.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Duplicate resume detected. This exact file has already been uploaded.")

    # ── 2. Call ML service for parsing ────────────────────
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            ml_resp = await client.post(
                settings.RESUME_ML_ENDPOINT,
                files={"file": (file.filename, content, file.content_type or "application/octet-stream")},
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to reach ML service: {exc}") from exc

    if ml_resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"ML service error ({ml_resp.status_code}): {ml_resp.text}")

    parsed: dict[str, Any] = ml_resp.json()

    # ── 3. Duplicate check by email ───────────────────────
    parsed_email = parsed.get("email")
    if parsed_email:
        email_check = await db.execute(select(Candidate).where(Candidate.email == parsed_email))
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"A candidate with email '{parsed_email}' already exists. Duplicate resume upload prevented.",
            )

    # ── 4. Save file to disk ──────────────────────────────
    safe_name = f"{file_hash[:16]}_{Path(file.filename or 'resume.pdf').name}"
    file_path = _UPLOADS_DIR / safe_name
    file_path.write_bytes(content)
    resume_file_url = f"/api/v1/candidates/files/{safe_name}"

    # ── 5. Extract resume text (from parsed_json or raw) ──
    resume_text = parsed.get("resume_text") or str(parsed)

    full_name = parsed.get("name") or parsed.get("full_name") or "Unknown"
    exp_years = float(parsed.get("experience_years") or 0)

    # ── 6. Compute ATS score ──────────────────────────────
    skills = parsed.get("skills", [])
    education = parsed.get("education", [])
    skill_score = min(50, len(skills) * 3)          # up to 50 pts
    exp_score = min(30, int(exp_years) * 3)          # up to 30 pts
    edu_score = 20 if education else 0               # 20 pts if education present
    ats_score = skill_score + exp_score + edu_score

    candidate = Candidate(
        full_name=full_name,
        email=parsed_email or f"unknown-{uuid.uuid4().hex[:8]}@placeholder.com",
        phone=parsed.get("phone"),
        location=parsed.get("location"),
        skills=skills,
        education=education,
        experience_years=exp_years,
        source="upload",
        resume_path=file.filename,
        resume_file_url=resume_file_url,
        resume_text=resume_text[:10000] if resume_text else None,
        resume_hash=file_hash,
        parsed_json=parsed,
        ats_score=min(100, ats_score),
    )

    db.add(candidate)
    await db.flush()
    await db.refresh(candidate)

    # ── 7. AI Summary ─────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            sum_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/ml/v1/summary",
                json={"name": full_name, "experience": int(exp_years), "skills": skills},
            )
            if sum_resp.status_code == 200:
                candidate.ai_summary = sum_resp.json().get("summary", "")
    except Exception as e:
        print(f"Summary generation failed: {e}")

    # ── 8. Skill graph ────────────────────────────────────
    try:
        from app.ml.skill_graph.skill_graph import build_skill_graph
        candidate.skill_graph_data = build_skill_graph(skills)
    except Exception as e:
        print(f"Skill graph failed: {e}")

    # ── 9. Fraud detection ────────────────────────────────
    try:
        from app.ml.fraud_detection.fraud_detector import run_fraud_detection
        candidate.fraud_flags = run_fraud_detection(
            resume_text=resume_text,
            skills=skills,
            experience_years=exp_years or None,
            education=education,
        )
    except Exception as e:
        print(f"Fraud detection failed: {e}")

    # ── 10. Embeddings ────────────────────────────────────
    try:
        from app.ml.embeddings.embedder import upsert_embedding
        upsert_embedding(str(candidate.id), resume_text or full_name)
    except Exception:
        pass

    await db.flush()
    await db.commit()
    return candidate


@router.get("/files/{filename}", summary="Serve uploaded resume file")
async def serve_resume_file(filename: str):
    """Stream the original uploaded PDF file."""
    file_path = _UPLOADS_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Resume file not found")
    # Security: ensure path doesn't escape uploads dir
    try:
        file_path.resolve().relative_to(_UPLOADS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/{candidate_id}/resume", summary="Get candidate resume file")
async def get_candidate_resume(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return the original uploaded PDF for a candidate."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not candidate.resume_file_url:
        raise HTTPException(status_code=404, detail="No resume file stored for this candidate")
    # Extract filename from URL
    filename = candidate.resume_file_url.split("/")[-1]
    file_path = _UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={candidate.full_name.replace(' ', '_')}_resume.pdf"},
    )


@router.get("", response_model=list[CandidateOut], summary="List all candidates")
async def list_candidates(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Return paginated list of candidates.
    Deduplicates by email — keeps the record with the highest experience_years
    (falls back to most recently created) so duplicate uploads never show twice.
    """
    from sqlalchemy import text as sa_text

    # Use a raw query for DISTINCT ON which SQLAlchemy ORM doesn't support natively
    raw = await db.execute(
        sa_text("""
            SELECT DISTINCT ON (email) *
            FROM candidates
            ORDER BY email, experience_years DESC NULLS LAST, created_at DESC
            LIMIT :limit OFFSET :skip
        """),
        {"limit": limit, "skip": skip},
    )
    rows = raw.mappings().all()

    # Re-fetch as ORM objects so response_model serialization works
    ids = [r["id"] for r in rows]
    if not ids:
        return []
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id.in_(ids))
        .order_by(Candidate.created_at.desc())
    )
    return result.scalars().all()


@router.post("/purge-duplicates", summary="Delete exact duplicate candidates (same name+email)")
async def purge_duplicates(db: AsyncSession = Depends(get_db)):
    """
    Hard-delete duplicate candidate rows that share the same email.
    Keeps the oldest record (lowest created_at) and deletes the rest.
    """
    from sqlalchemy import text as sa_text
    # Find emails with more than one row
    dup_result = await db.execute(
        select(Candidate.email, func.count(Candidate.id).label("cnt"))
        .group_by(Candidate.email)
        .having(func.count(Candidate.id) > 1)
    )
    dup_emails = [row.email for row in dup_result]

    deleted_total = 0
    for email in dup_emails:
        rows_result = await db.execute(
            select(Candidate)
            .where(Candidate.email == email)
            .order_by(Candidate.created_at.asc())
        )
        rows = rows_result.scalars().all()
        # Keep first (oldest), delete the rest
        for dup in rows[1:]:
            await db.delete(dup)
            deleted_total += 1

    await db.commit()
    return {"deleted": deleted_total, "duplicate_emails_found": len(dup_emails)}


@router.get("/analytics", summary="Get recruitment analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Get recruitment analytics."""
    # Total candidates
    total_result = await db.execute(select(func.count(Candidate.id)))
    total_candidates = total_result.scalar() or 0
    
    # Fetch all candidates to compute ATS average (including profile-based fallback)
    all_candidates_result = await db.execute(select(Candidate))
    all_candidates = all_candidates_result.scalars().all()
    
    # Compute ATS score for each candidate — use stored value or calculate from profile
    def profile_ats(c):
        if c.ats_score and c.ats_score > 0:
            return float(c.ats_score)
        score = 0
        if c.full_name and c.full_name != "Unknown": score += 10
        if c.email and "placeholder" not in c.email: score += 10
        if c.phone: score += 10
        if c.location: score += 8
        if c.experience_years: score += min(15, int(c.experience_years) * 2)
        if c.skills: score += min(17, len(c.skills) * 2)
        if c.education: score += 10
        if c.ai_summary: score += 10
        if c.parsed_json and len(c.parsed_json) > 3: score += 10
        return min(100, score)
    
    scores = [profile_ats(c) for c in all_candidates]
    avg_ats_score = sum(scores) / len(scores) if scores else 0
    
    # Candidates by source
    source_result = await db.execute(
        select(Candidate.source, func.count(Candidate.id))
        .group_by(Candidate.source)
    )
    sources = {}
    for source, count in source_result:
        sources[source or "unknown"] = count
    
    source_percentages = {}
    if total_candidates > 0:
        for source, count in sources.items():
            source_percentages[source] = round((count / total_candidates) * 100, 1)
    
    # Recent candidates (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_result = await db.execute(
        select(func.count(Candidate.id))
        .where(Candidate.created_at >= thirty_days_ago)
    )
    recent_candidates = recent_result.scalar() or 0
    
    # Candidates with summaries
    summary_result = await db.execute(
        select(func.count(Candidate.id))
        .where(Candidate.ai_summary != None)
        .where(Candidate.ai_summary != "")
    )
    candidates_with_summaries = summary_result.scalar() or 0
    
    return {
        "total_candidates": total_candidates,
        "avg_ats_score": round(avg_ats_score, 1),
        "recent_candidates_30d": recent_candidates,
        "candidates_with_summaries": candidates_with_summaries,
        "summary_completion_rate": round((candidates_with_summaries / total_candidates) * 100, 1) if total_candidates > 0 else 0,
        "sources": sources,
        "source_percentages": source_percentages,
        "hiring_funnel": {
            "applied": total_candidates,
            "screening": int(total_candidates * 0.6),
            "interviewing": int(total_candidates * 0.25),
            "offers": int(total_candidates * 0.05),
            "hired": int(total_candidates * 0.02)
        }
    }


@router.post("/recalculate-experience", summary="Fix experience_years=0 for existing candidates")
async def recalculate_experience(db: AsyncSession = Depends(get_db)):
    """
    For every candidate where experience_years is 0 or null but parsed_json
    contains work_experience entries or an experience_years value, recalculate
    and persist the correct value.
    """
    result = await db.execute(
        select(Candidate).where(
            (Candidate.experience_years == None) | (Candidate.experience_years == 0)
        )
    )
    candidates = result.scalars().all()
    fixed = 0
    for c in candidates:
        pj = c.parsed_json or {}
        # Use stored experience_years from parsed_json first
        exp = pj.get("experience_years") or 0
        # If still 0, estimate from work_experience entries
        if not exp:
            work_exp = pj.get("work_experience") or []
            total_months = 0
            for e in work_exp:
                start_str = str(e.get("start", ""))
                end_str = str(e.get("end", "present"))
                sm = re.search(r'(20\d{2}|19\d{2})', start_str)
                em = re.search(r'(20\d{2}|19\d{2})', end_str)
                if sm:
                    sy = int(sm.group(1))
                    ey = int(em.group(1)) if em else 2026
                    total_months += max(0, (ey - sy) * 12)
            if total_months > 0:
                exp = round(min(total_months / 12.0, 50), 1)
        if exp and exp > 0:
            c.experience_years = exp
            fixed += 1
    await db.commit()
    return {"fixed": fixed, "total_checked": len(candidates)}


@router.post("/generate-all-summaries", summary="Generate summaries for all candidates missing one")
async def generate_all_summaries(db: AsyncSession = Depends(get_db)):
    """Bulk generate AI summaries for candidates that don't have one."""
    result = await db.execute(
        select(Candidate).where(
            (Candidate.ai_summary == None) | (Candidate.ai_summary == "")
        )
    )
    candidates = result.scalars().all()
    
    success, failed = 0, 0
    async with httpx.AsyncClient(timeout=60) as client:
        for candidate in candidates:
            try:
                ml_resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/ml/v1/summary",
                    json={
                        "name": candidate.full_name,
                        "experience": int(candidate.experience_years) if candidate.experience_years else 0,
                        "skills": candidate.skills or []
                    }
                )
                if ml_resp.status_code == 200:
                    candidate.ai_summary = ml_resp.json().get("summary", "")
                    await db.flush()
                    success += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
    
    await db.commit()
    return {"generated": success, "failed": failed, "total": len(candidates)}



async def get_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return a single candidate by UUID."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateOut, summary="Update candidate")
async def update_candidate(
    candidate_id: uuid.UUID,
    body: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update a candidate."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(candidate, key, value)

    await db.flush()
    await db.refresh(candidate)
    return candidate


@router.delete("/{candidate_id}", status_code=204, summary="Delete candidate")
async def delete_candidate(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Hard-delete a candidate and their stored resume file."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    # Remove file from disk if stored
    if candidate.resume_file_url:
        filename = candidate.resume_file_url.split("/")[-1]
        file_path = _UPLOADS_DIR / filename
        if file_path.exists():
            file_path.unlink(missing_ok=True)
    await db.delete(candidate)
    await db.commit()


@router.get("/{candidate_id}/summary", response_model=CandidateSummaryOut, summary="AI summary")
async def get_summary(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Generate or return a 3-line AI summary for the candidate.
    
    This endpoint:
    1. Fetches candidate from PostgreSQL
    2. Checks if summary already exists (cached)
    3. If not, calls ML service to generate summary
    4. Stores summary in database for future use
    5. Returns summary
    """
    # Step 1: Fetch candidate from database
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Step 2: Return cached summary if exists
    if candidate.ai_summary:
        return CandidateSummaryOut(candidate_id=candidate.id, summary=candidate.ai_summary)

    # Step 3: Call ML service to generate summary
    try:
        # Prepare data for ML service
        candidate_name = candidate.full_name
        candidate_experience = int(candidate.experience_years) if candidate.experience_years else 0
        candidate_skills = candidate.skills or []
        
        # Call ML summary endpoint
        async with httpx.AsyncClient(timeout=60) as client:
            ml_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/ml/v1/summary",
                json={
                    "name": candidate_name,
                    "experience": candidate_experience,
                    "skills": candidate_skills
                }
            )
        
        if ml_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"ML service summary generation failed: {ml_resp.text}"
            )
        
        ml_result = ml_resp.json()
        summary = ml_result.get("summary", "")
        
        # Step 4: Store summary in database for caching
        candidate.ai_summary = summary
        await db.flush()
        await db.commit()
        
        # Step 5: Return summary
        return CandidateSummaryOut(candidate_id=candidate.id, summary=summary)
    
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach ML service: {exc}"
        ) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summary generation failed: {str(e)}"
        )


@router.get("/{candidate_id}/fraud-report", response_model=FraudReportOut, summary="Fraud report")
async def get_fraud_report(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Run fraud detection on a candidate."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    from app.ml.fraud_detection.fraud_detector import run_fraud_detection
    report = run_fraud_detection(
        resume_text=str(candidate.parsed_json) if candidate.parsed_json else "",
        skills=candidate.skills or [],
        experience_years=float(candidate.experience_years) if candidate.experience_years else None,
        education=candidate.education or [],
    )

    candidate.fraud_flags = report
    await db.flush()

    return FraudReportOut(
        candidate_id=candidate.id,
        risk_score=report["risk_score"],
        flags=report["flags"],
    )


@router.get("/{candidate_id}/skill-graph", response_model=SkillGraphOut, summary="Skill graph")
async def get_skill_graph(candidate_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generate radar-chart skill graph data for a candidate."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    from app.ml.skill_graph.skill_graph import build_skill_graph
    graph = build_skill_graph(candidate.skills or [])

    candidate.skill_graph_data = graph
    await db.flush()

    return SkillGraphOut(candidate_id=candidate.id, skill_graph=graph)


@router.post("/reindex-embeddings", summary="Reindex all candidates into ChromaDB")
async def reindex_all_embeddings(db: AsyncSession = Depends(get_db)):
    """
    Fetch all candidates from PostgreSQL and reindex them into ChromaDB
    for semantic search. This ensures all candidates are searchable.
    """
    try:
        # Fetch all candidates from database
        result = await db.execute(select(Candidate))
        candidates = result.scalars().all()
        
        if not candidates:
            return {
                "status": "success",
                "indexed_candidates": 0,
                "message": "No candidates found in database"
            }
        
        # Prepare candidate data for ML service
        candidates_data = []
        for candidate in candidates:
            # Use parsed_json text or construct from fields
            if candidate.parsed_json:
                text = str(candidate.parsed_json)
            else:
                # Construct text from candidate fields
                text = f"{candidate.full_name} {candidate.email or ''} "
                text += f"Skills: {', '.join(candidate.skills or [])} "
                text += f"Experience: {candidate.experience_years or 0} years "
                text += f"Location: {candidate.location or ''}"
            
            candidates_data.append({
                "id": str(candidate.id),
                "text": text
            })
        
        # Call ML service reindex endpoint
        async with httpx.AsyncClient(timeout=300) as client:
            ml_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/ml/v1/reindex_embeddings",
                json={"candidates": candidates_data}
            )
        
        if ml_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"ML service reindex failed: {ml_resp.text}"
            )
        
        result = ml_resp.json()
        return result
    
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach ML service: {exc}"
        ) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reindexing failed: {str(e)}"
        )


@router.post("/semantic-search", summary="Semantic search for candidates")
async def semantic_search_candidates(
    query: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search for candidates using ChromaDB embeddings,
    then enrich results with full candidate data from PostgreSQL.
    
    Steps:
    1. Call ML service to get candidate IDs from vector search
    2. Fetch full candidate records from PostgreSQL
    3. Return enriched results with name, skills, experience
    """
    try:
        # Step 1: Call ML service for vector search
        async with httpx.AsyncClient(timeout=60) as client:
            ml_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/ml/v1/semantic_search",
                params={"query": query, "n_results": limit}
            )
        
        if ml_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"ML service search failed: {ml_resp.text}"
            )
        
        ml_results = ml_resp.json()
        
        # Extract candidate IDs and similarity scores
        candidate_ids = []
        similarity_map = {}
        
        for candidate in ml_results.get("candidates", []):
            candidate_id = candidate.get("id")
            if candidate_id:
                try:
                    # Convert string UUID to UUID object
                    uuid_obj = uuid.UUID(candidate_id)
                    candidate_ids.append(uuid_obj)
                    similarity_map[str(uuid_obj)] = candidate.get("similarity_score", 0)
                except ValueError:
                    continue
        
        if not candidate_ids:
            return {
                "query": query,
                "total_results": 0,
                "candidates": []
            }
        
        # Step 2: Fetch full candidate records from PostgreSQL
        result = await db.execute(
            select(Candidate).where(Candidate.id.in_(candidate_ids))
        )
        candidates = result.scalars().all()
        
        # Step 3: Build enriched response
        enriched_candidates = []
        for candidate in candidates:
            candidate_id_str = str(candidate.id)
            enriched_candidates.append({
                "id": candidate_id_str,
                "name": candidate.full_name,
                "skills": candidate.skills or [],
                "experience_years": float(candidate.experience_years) if candidate.experience_years else 0,
                "similarity_score": similarity_map.get(candidate_id_str, 0)
            })
        
        # Sort by similarity score descending (highest first)
        enriched_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "query": query,
            "total_results": len(enriched_candidates),
            "candidates": enriched_candidates
        }
    
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach ML service: {exc}"
        ) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/{candidate_id}/ats-score", summary="Calculate ATS score for candidate")
async def calculate_ats_score(
    candidate_id: uuid.UUID,
    job_description: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate ATS (Applicant Tracking System) score for a candidate against a job description.
    
    This endpoint:
    1. Fetches the candidate from PostgreSQL
    2. Extracts resume text from parsed_json
    3. Calls ML service to calculate ATS score
    4. Returns score with matched and missing skills
    
    Parameters:
    - candidate_id: UUID of the candidate
    - job_description: Job description text to match against
    
    Returns:
    - candidate_id: UUID
    - candidate_name: Full name
    - ats_score: Similarity score (0-100)
    - matched_skills: Skills that match the job
    - missing_skills: Skills in job but not in candidate
    """
    try:
        # Step 1: Fetch candidate from database
        result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Step 2: Extract resume text from parsed_json or construct from fields
        resume_text = ""
        
        if candidate.parsed_json:
            # Convert parsed_json to text representation
            resume_text = str(candidate.parsed_json)
        else:
            # Construct text from candidate fields
            resume_text = f"{candidate.full_name}\n"
            resume_text += f"Email: {candidate.email}\n"
            if candidate.phone:
                resume_text += f"Phone: {candidate.phone}\n"
            if candidate.location:
                resume_text += f"Location: {candidate.location}\n"
            if candidate.skills:
                resume_text += f"Skills: {', '.join(candidate.skills)}\n"
            if candidate.experience_years:
                resume_text += f"Experience: {candidate.experience_years} years\n"
            if candidate.education:
                resume_text += f"Education: {str(candidate.education)}\n"
        
        # Step 3: Call ML service ATS endpoint
        async with httpx.AsyncClient(timeout=60) as client:
            ml_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/ml/v1/ats_score",
                params={
                    "resume_text": resume_text,
                    "jd_text": job_description
                }
            )
        
        if ml_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"ML service ATS calculation failed: {ml_resp.text}"
            )
        
        ml_result = ml_resp.json()
        ats_score_value = ml_result.get("ats_score", 0)
        
        # Step 4: Extract skills from job description for matching with normalization
        # Skill alias dictionary (same as ML service)
        skill_aliases = {
            "py": "python", "js": "javascript", "ts": "typescript",
            "nodejs": "node.js", "node": "node.js", "reactjs": "react", "vuejs": "vue",
            "springboot": "spring boot", "ml": "machine learning", "dl": "deep learning",
            "ai": "artificial intelligence", "tf": "tensorflow", "np": "numpy",
            "pd": "pandas", "sklearn": "scikit-learn", "postgres": "postgresql",
            "mongo": "mongodb", "k8s": "kubernetes", "gql": "graphql"
        }
        
        # Normalize job description
        jd_lower = job_description.lower()
        for alias, canonical in skill_aliases.items():
            jd_lower = jd_lower.replace(alias, canonical)
        
        # Normalize candidate skills
        normalized_candidate_skills = []
        for skill in (candidate.skills or []):
            skill_lower = skill.lower()
            # Replace alias if exists
            normalized_skill = skill_aliases.get(skill_lower, skill_lower)
            normalized_candidate_skills.append(normalized_skill)
        
        # Common tech skills to check (expanded with aliases)
        common_skills = [
            "python", "java", "javascript", "typescript", "react", "angular", "vue",
            "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
            "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
            "aws", "azure", "gcp", "git", "ci/cd", "rest api", "graphql",
            "machine learning", "deep learning", "tensorflow", "pytorch", "numpy", "pandas",
            "scikit-learn", "html", "css", "c++", "c#", "go", "rust", "php", "ruby"
        ]
        
        # Find skills mentioned in normalized job description
        import re
        jd_skills = []
        for skill in common_skills:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, jd_lower):
                jd_skills.append(skill)
        
        # Determine matched and missing skills using normalized data
        matched_skills = []
        missing_skills = []
        
        for jd_skill in jd_skills:
            # Check if candidate has this skill (fuzzy match on normalized skills)
            if any(jd_skill in candidate_skill or candidate_skill in jd_skill 
                   for candidate_skill in normalized_candidate_skills):
                matched_skills.append(jd_skill)
            else:
                missing_skills.append(jd_skill)
        
        # Step 5: Return comprehensive response
        return {
            "candidate_id": str(candidate.id),
            "candidate_name": candidate.full_name,
            "ats_score": ats_score_value,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "candidate_skills": candidate.skills or [],
            "experience_years": float(candidate.experience_years) if candidate.experience_years else 0
        }
    
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach ML service: {exc}"
        ) from exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ATS calculation failed: {str(e)}"
        )



# ── VIDEO SCORES (also before wildcard) ──────────────────────────────────────

@router.post("/{candidate_id}/video-scores", summary="Update video screening scores")
async def update_video_scores(
    candidate_id: uuid.UUID,
    confidence_score: float,
    technical_score: float,
    db: AsyncSession = Depends(get_db),
):
    """Update candidate with video screening scores."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate.confidence_score = confidence_score
    candidate.technical_score = technical_score
    candidate.video_screening_completed = "completed"
    await db.commit()
    await db.refresh(candidate)
    return {
        "candidate_id": str(candidate.id),
        "confidence_score": float(candidate.confidence_score),
        "technical_score": float(candidate.technical_score),
        "status": candidate.video_screening_completed,
    }


# ── UPLOAD RESUME FOR EXISTING CANDIDATE ─────────────────────────────────────

@router.post("/{candidate_id}/upload-resume", summary="Upload resume for existing candidate")
async def upload_resume_for_candidate(
    candidate_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and parse a resume for an existing candidate (from portal flow)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()

    # Save file
    safe_name = f"{file_hash[:16]}_{Path(file.filename or 'resume.pdf').name}"
    file_path = _UPLOADS_DIR / safe_name
    file_path.write_bytes(content)
    resume_file_url = f"/api/v1/candidates/files/{safe_name}"

    # Parse via ML service
    parsed = {}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            ml_resp = await client.post(
                settings.RESUME_ML_ENDPOINT,
                files={"file": (file.filename, content, file.content_type or "application/octet-stream")},
            )
            if ml_resp.status_code == 200:
                parsed = ml_resp.json()
    except Exception as e:
        print(f"ML parsing failed: {e}")
        # Continue with basic data — parsing failure shouldn't block upload

    # Update candidate with parsed data
    skills = parsed.get("skills", [])
    education = parsed.get("education", [])
    exp_years = float(parsed.get("experience_years", 0))
    resume_text = parsed.get("resume_text", "")
    parsed_name = parsed.get("name") or parsed.get("full_name", "")

    # Only update name if parsed name is valid and existing name is missing
    if parsed_name and parsed_name != "Unknown" and (not candidate.full_name or candidate.full_name == "Unknown"):
        candidate.full_name = parsed_name

    candidate.resume_path = file.filename
    candidate.resume_file_url = resume_file_url
    candidate.resume_text = resume_text[:10000] if resume_text else None
    candidate.resume_hash = file_hash
    candidate.parsed_json = parsed or {}

    if skills:
        candidate.skills = skills
    if education:
        candidate.education = education
    if exp_years > 0:
        candidate.experience_years = exp_years
    if parsed.get("phone"):
        candidate.phone = parsed["phone"]
    if parsed.get("location"):
        candidate.location = parsed["location"]

    # ATS score
    skill_score = min(50, len(skills) * 3)
    exp_score = min(30, int(exp_years) * 3)
    edu_score = 20 if education else 0
    candidate.ats_score = min(100, skill_score + exp_score + edu_score)

    # AI Summary
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            sum_resp = await client.post(
                f"{settings.ML_SERVICE_URL}/ml/v1/summary",
                json={"name": candidate.full_name, "experience": int(exp_years), "skills": skills},
            )
            if sum_resp.status_code == 200:
                candidate.ai_summary = sum_resp.json().get("summary", "")
    except Exception:
        pass

    # Skill graph
    try:
        from app.ml.skill_graph.skill_graph import build_skill_graph
        candidate.skill_graph_data = build_skill_graph(skills)
    except Exception:
        pass

    # Fraud detection
    try:
        from app.ml.fraud_detection.fraud_detector import run_fraud_detection
        candidate.fraud_flags = run_fraud_detection(
            resume_text=resume_text, skills=skills,
            experience_years=exp_years or None, education=education,
        )
    except Exception:
        pass

    # Run integrity check
    try:
        from app.services.candidate_integrity_service import calculate_fraud_score
        integrity = await calculate_fraud_score(candidate, db)
        candidate.fraud_score = integrity["fraud_score"]
        candidate.is_flagged = integrity["is_flagged"]
        candidate.is_duplicate = integrity["is_duplicate"]
        candidate.fraud_reason = integrity.get("fraud_reason")
        candidate.verification_status = "flagged" if integrity["is_flagged"] else "valid"
    except Exception as e:
        print(f"Integrity check failed: {e}")

    await db.commit()
    await db.refresh(candidate)

    return {
        "id": str(candidate.id),
        "full_name": candidate.full_name,
        "email": candidate.email,
        "skills": candidate.skills or [],
        "experience_years": float(candidate.experience_years) if candidate.experience_years else 0,
        "ats_score": float(candidate.ats_score) if candidate.ats_score else 0,
        "parse_success": bool(parsed),
        "skills_found": len(skills),
        "status": "parsed",
        "message": f"Resume parsed successfully. Found {len(skills)} skills and {exp_years} years of experience.",
    }


# ── HIRE CANDIDATE (with offer letter) ───────────────────────────────────────

class HireRequest(BaseModel):
    position: str = "Software Engineer"
    salary: str = "As per company standards"
    start_date: str = ""
    department: str = "Engineering"

@router.post("/{candidate_id}/hire", summary="Hire candidate and send offer letter")
async def hire_candidate(
    candidate_id: uuid.UUID,
    body: HireRequest,
    db: AsyncSession = Depends(get_db),
):
    """Mark candidate as hired and send offer letter PDF via email."""
    try:
        logger.info(f"Hire request for candidate {candidate_id} with data: {body}")
        
        result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
        candidate = result.scalar_one_or_none()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        logger.info(f"Found candidate: {candidate.full_name} ({candidate.email})")

        candidate.status = "hired"
        candidate.verification_status = "hired"

        # Send offer letter email with dynamically generated PDF attachment
        email_sent = False
        candidate_email = candidate.email
        
        logger.info(f"Attempting to send email to: {candidate_email}")
        
        if candidate_email and "placeholder" not in candidate_email:
            try:
                import smtplib
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                from email.mime.base import MIMEBase
                from email import encoders

                today = datetime.now().strftime("%B %d, %Y")
                start = body.start_date or (datetime.now() + timedelta(days=30)).strftime("%B %d, %Y")

            offer_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #0f766e, #14b8a6); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Job Offer Letter</h1>
                    <p style="color: rgba(255,255,255,0.8); margin-top: 8px;">HireAI</p>
                </div>
                <div style="border: 1px solid #e5e7eb; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
                    <p style="font-size: 14px; color: #6b7280;">Date: {today}</p>
                    <p style="font-size: 16px; color: #111827;">Dear <strong>{candidate.full_name}</strong>,</p>

                    <p>We are pleased to inform you that you have been selected to join HireAI.
                    Based on your profile and qualifications, we would like to offer you the
                    opportunity to become a part of our team.</p>

                    <div style="background: #f0f9ff; border-left: 4px solid #0f766e; padding: 16px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="padding: 8px 0; color: #6b7280;">Position:</td><td style="padding: 8px 0; font-weight: bold; color: #111827;">{body.position}</td></tr>
                            <tr><td style="padding: 8px 0; color: #6b7280;">Department:</td><td style="padding: 8px 0; font-weight: bold; color: #111827;">{body.department}</td></tr>
                            <tr><td style="padding: 8px 0; color: #6b7280;">Compensation:</td><td style="padding: 8px 0; font-weight: bold; color: #111827;">{body.salary}</td></tr>
                            <tr><td style="padding: 8px 0; color: #6b7280;">Start Date:</td><td style="padding: 8px 0; font-weight: bold; color: #111827;">{start}</td></tr>
                        </table>
                    </div>

                    <p>This letter serves as a preliminary offer of employment confirming your
                    selection at HireAI. We are excited about the possibility of you contributing to
                    our growing organization.</p>

                    <p>Please confirm your acceptance by replying to this email within <strong>7 business days</strong>.</p>

                    <p>We look forward to welcoming you to HireAI.</p>

                    <p style="margin-top: 30px;">
                        Sincerely,<br/>
                        <strong>Hiring Team</strong><br/>
                        <strong>HireAI</strong><br/>
                        <a href="mailto:recruiting@example.com">recruiting@example.com</a>
                    </p>
                </div>
            </body>
            </html>
            """

            msg = MIMEMultipart("mixed")
            msg["Subject"] = f"🎉 Job Offer Letter — {body.position} at HireAI"
            msg["From"] = settings.EMAIL_ADDRESS or "recruiting@example.com"
            msg["To"] = candidate_email

            # Attach HTML body
            html_part = MIMEMultipart("alternative")
            html_part.attach(MIMEText(offer_html, "html"))
            msg.attach(html_part)

            # Generate and attach offer letter PDF dynamically
            try:
                from app.services.generate_offer_letter import generate_offer_letter_pdf
                pdf_bytes = generate_offer_letter_pdf(
                    candidate_name=candidate.full_name,
                    position=body.position,
                    department=body.department,
                    salary=body.salary,
                    start_date=start,
                )
                pdf_attachment = MIMEBase("application", "pdf")
                pdf_attachment.set_payload(pdf_bytes)
                encoders.encode_base64(pdf_attachment)
                safe_name = candidate.full_name.replace(' ', '_').replace('"', '').replace("'", '')
                pdf_attachment.add_header(
                    "Content-Disposition",
                    f"attachment; filename=HireAI_Offer_Letter_{safe_name}.pdf",
                )
                msg.attach(pdf_attachment)
            except Exception as pdf_err:
                print(f"Offer letter PDF generation failed: {pdf_err}")
                # Email will still be sent without PDF attachment

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(
                    settings.EMAIL_ADDRESS or "your-email@example.com",
                    settings.EMAIL_PASSWORD or "your-app-password",
                )
                smtp.send_message(msg)
            email_sent = True
        except Exception as e:
            logger.error(f"Offer email failed: {e}")
            print(f"Offer email failed: {e}")

        # Push to OrangeHRM (optional - don't fail if this fails)
        orangehrm_result = {"pushed": False, "message": "Not attempted"}
        try:
            from app.services.orangehrm_service import push_candidate_to_orangehrm
            orangehrm_result = await push_candidate_to_orangehrm({
                "full_name": candidate.full_name,
                "first_name": candidate.first_name,
                "last_name": candidate.last_name,
                "email": candidate.email,
                "phone": candidate.phone or candidate.mobile_number,
                "skills": candidate.skills or [],
                "ats_score": float(candidate.ats_score) if candidate.ats_score else 0,
            })
        except ImportError:
            logger.warning("OrangeHRM service not available")
            orangehrm_result = {"pushed": False, "message": "Service not available"}
        except Exception as e:
            logger.error(f"OrangeHRM push failed: {e}")
            print(f"OrangeHRM push failed: {e}")
            orangehrm_result = {"pushed": False, "message": str(e)}

        await db.commit()

        return {
            "candidate_id": str(candidate.id),
            "candidate_name": candidate.full_name,
            "status": "hired",
            "offer_email_sent": email_sent,
            "offer_sent_to": candidate_email if email_sent else None,
            "orangehrm": orangehrm_result,
            "message": f"{'Offer letter sent to ' + candidate_email if email_sent else 'Candidate hired (email delivery failed)'}",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hire candidate failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to hire candidate: {str(e)}")


# ── SEND TECHNICAL ASSESSMENT TO CANDIDATE ───────────────────────────────────

class SendAssessmentRequest(BaseModel):
    assessment_type: str = "coding"
    message: str = ""

@router.post("/{candidate_id}/send-assessment", summary="Send technical assessment to candidate email")
async def send_assessment_to_candidate(
    candidate_id: uuid.UUID,
    body: SendAssessmentRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Send a technical assessment invitation to the candidate's email (not HR)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if body is None:
        body = SendAssessmentRequest()

    candidate_email = candidate.email
    if not candidate_email or "placeholder" in candidate_email:
        raise HTTPException(status_code=400, detail="Candidate has no valid email address")

    assessment_labels = {
        "coding": "Coding Challenge",
        "system-design": "System Design Assessment",
        "take-home": "Take-Home Project",
        "mcq": "MCQ Technical Quiz",
    }
    label = assessment_labels.get(body.assessment_type, "Technical Assessment")

    email_sent = False
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        assessment_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #7c3aed, #2563eb); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">📝 Technical Assessment Invitation</h1>
                <p style="color: rgba(255,255,255,0.8); margin-top: 8px;">HireAI</p>
            </div>
            <div style="border: 1px solid #e5e7eb; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
                <p style="font-size: 16px; color: #111827;">Dear <strong>{candidate.full_name}</strong>,</p>

                <p>Congratulations! You have been <strong>shortlisted</strong> for the next round of our hiring process.</p>

                <p>We would like to invite you to complete the following assessment:</p>

                <div style="background: #f5f3ff; border-left: 4px solid #7c3aed; padding: 16px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                    <h3 style="margin: 0 0 8px 0; color: #7c3aed;">{label}</h3>
                    <p style="margin: 0; color: #374151;">Please log in to the candidate portal to take the assessment.</p>
                    <p style="margin: 8px 0 0 0; color: #6b7280; font-size: 13px;">Portal: <a href="http://localhost:5173/candidate-portal">Candidate Portal</a></p>
                </div>

                {f'<p style="color: #374151;"><strong>Note from HR:</strong> {body.message}</p>' if body.message else ''}

                <p><strong>Important:</strong></p>
                <ul style="color: #374151;">
                    <li>Complete the assessment within 48 hours</li>
                    <li>Ensure stable internet connection</li>
                    <li>Each question is timed individually</li>
                </ul>

                <p>Good luck! We look forward to seeing your results.</p>

                <p style="margin-top: 30px;">
                    Best Regards,<br/>
                    <strong>HR Team</strong><br/>
                    HireAI
                </p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📝 {label} — HireAI"
        msg["From"] = settings.EMAIL_ADDRESS or "recruiting@example.com"
        msg["To"] = candidate_email
        msg.attach(MIMEText(assessment_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(
                settings.EMAIL_ADDRESS or "your-email@example.com",
                settings.EMAIL_PASSWORD or "your-app-password",
            )
            smtp.send_message(msg)
        email_sent = True
        candidate.status = "assessment_sent"
        await db.commit()
    except Exception as e:
        print(f"Assessment email failed: {e}")

    return {
        "candidate_id": str(candidate.id),
        "candidate_name": candidate.full_name,
        "email_sent": email_sent,
        "sent_to": candidate_email,
        "assessment_type": body.assessment_type,
        "message": f"Assessment invitation sent to {candidate_email}" if email_sent else "Failed to send assessment email",
    }


# ── CANDIDATE VALIDATE (Integrity Check) ─────────────────────────────────────

@router.post("/validate", summary="Validate candidate integrity")
async def validate_candidate(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Run full integrity validation on a candidate."""
    candidate_id = body.get("candidate_id")
    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id is required")

    try:
        cid = uuid.UUID(candidate_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid candidate_id format")

    result = await db.execute(select(Candidate).where(Candidate.id == cid))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    from app.services.candidate_integrity_service import validate_candidate_pipeline
    validation = await validate_candidate_pipeline(candidate, db)

    # Update candidate fields
    candidate.fraud_score = validation["validation_result"]["fraud_score"]
    candidate.is_flagged = validation["validation_result"]["is_flagged"]
    candidate.is_duplicate = validation["validation_result"]["is_duplicate"]
    candidate.fraud_reason = validation["validation_result"].get("fraud_reason")
    candidate.verification_status = "flagged" if validation["validation_result"]["is_flagged"] else "valid"
    await db.commit()

    return {
        "is_duplicate": validation["validation_result"]["is_duplicate"],
        "fraud_score": validation["validation_result"]["fraud_score"],
        "status": "flagged" if validation["validation_result"]["is_flagged"] else "valid",
        "recommendation": validation["recommendation"],
        "should_block": validation["should_block"],
        "flags": validation["validation_result"]["flags"],
    }


# ── ORANGEHRM SYNC ───────────────────────────────────────────────────────────

@router.post("/sync-orangehrm", summary="Sync valid candidates to OrangeHRM")
async def sync_to_orangehrm(db: AsyncSession = Depends(get_db)):
    """Push all valid (non-flagged) candidates to OrangeHRM recruitment module."""
    result = await db.execute(select(Candidate))
    candidates = result.scalars().all()

    candidates_data = []
    for c in candidates:
        # Skip invalid candidates
        if not c.full_name or c.full_name in ("Unknown", "null", "undefined"):
            continue
        if c.is_flagged:
            continue
        candidates_data.append({
            "full_name": c.full_name,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone or c.mobile_number,
            "skills": c.skills or [],
            "ats_score": float(c.ats_score) if c.ats_score else 0,
            "is_flagged": c.is_flagged or False,
            "fraud_score": float(c.fraud_score) if c.fraud_score else 0,
        })

    from app.services.orangehrm_service import sync_all_candidates_to_orangehrm
    result = await sync_all_candidates_to_orangehrm(candidates_data)
    return result


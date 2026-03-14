"""
AI service endpoints - OpenAI summary generation and regeneration.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models.candidate import Candidate
from app.models.user import User
from app.routers.auth_router import get_current_user
from app.services.openai_service import generate_ai_summary, regenerate_summary_for_candidate

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────────────


class AISummaryRequest(BaseModel):
    """Request to generate AI summary."""
    resume_text: str
    skills: List[str]
    experience_years: float
    name: Optional[str] = None


class AISummaryResponse(BaseModel):
    """AI summary response."""
    summary: Optional[str]
    success: bool
    error: Optional[str] = None


class RegenerateSummaryRequest(BaseModel):
    """Request to regenerate summary for existing candidate."""
    candidate_id: UUID


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/summary", response_model=AISummaryResponse)
async def create_ai_summary(
    request: AISummaryRequest,
):
    """
    Generate AI-powered executive summary using OpenAI.
    
    This endpoint is called during resume processing to generate
    professional candidate summaries.
    """
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-placeholder":
        logger.error("OpenAI API key not configured")
        return AISummaryResponse(
            summary=None,
            success=False,
            error="OpenAI API key not configured"
        )
    
    logger.info("Generating AI summary via OpenAI API")
    
    summary = await generate_ai_summary(
        resume_text=request.resume_text,
        skills=request.skills,
        experience_years=request.experience_years,
        name=request.name
    )
    
    if summary:
        return AISummaryResponse(
            summary=summary,
            success=True
        )
    else:
        return AISummaryResponse(
            summary=None,
            success=False,
            error="OpenAI API call failed - check logs for details"
        )


@router.post("/regenerate-summary", response_model=AISummaryResponse)
async def regenerate_candidate_summary(
    request: RegenerateSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate AI summary for an existing candidate.
    
    This is useful for updating candidates that have static template summaries.
    Only HR users can regenerate summaries.
    """
    
    if current_user.role != "HR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR users can regenerate summaries"
        )
    
    # Fetch candidate
    result = await db.execute(
        select(Candidate).where(Candidate.id == request.candidate_id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Check if we have necessary data
    if not candidate.resume_text:
        raise HTTPException(
            status_code=400,
            detail="Candidate has no resume text - cannot generate summary"
        )
    
    # Regenerate summary
    summary = await regenerate_summary_for_candidate(
        candidate_id=str(candidate.id),
        resume_text=candidate.resume_text,
        skills=candidate.skills or [],
        experience_years=float(candidate.experience_years or 0),
        name=candidate.full_name
    )
    
    if summary:
        # Update candidate record
        candidate.ai_summary = summary
        await db.commit()
        
        logger.info(f"Updated AI summary for candidate {candidate.id}")
        
        return AISummaryResponse(
            summary=summary,
            success=True
        )
    else:
        return AISummaryResponse(
            summary=None,
            success=False,
            error="Failed to generate summary - check OpenAI API key and logs"
        )


@router.post("/batch-regenerate-summaries")
async def batch_regenerate_summaries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch regenerate AI summaries for all candidates with static templates.
    
    This endpoint identifies candidates with template-style summaries and
    regenerates them using OpenAI.
    
    Only HR users can run batch operations.
    """
    
    if current_user.role != "HR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR users can run batch operations"
        )
    
    # Find candidates with static summaries (containing "skilled professional")
    result = await db.execute(
        select(Candidate).where(
            Candidate.ai_summary.ilike("%skilled professional%")
        )
    )
    candidates = result.scalars().all()
    
    logger.info(f"Found {len(candidates)} candidates with static summaries")
    
    success_count = 0
    failed_count = 0
    
    for candidate in candidates:
        if not candidate.resume_text:
            logger.warning(f"Skipping candidate {candidate.id} - no resume text")
            failed_count += 1
            continue
        
        summary = await regenerate_summary_for_candidate(
            candidate_id=str(candidate.id),
            resume_text=candidate.resume_text,
            skills=candidate.skills or [],
            experience_years=float(candidate.experience_years or 0),
            name=candidate.full_name
        )
        
        if summary:
            candidate.ai_summary = summary
            success_count += 1
        else:
            failed_count += 1
    
    await db.commit()
    
    return {
        "total_candidates": len(candidates),
        "success": success_count,
        "failed": failed_count,
        "message": f"Regenerated {success_count} summaries, {failed_count} failed"
    }


@router.get("/check-openai-config")
async def check_openai_configuration():
    """
    Check if OpenAI is properly configured.
    
    Returns configuration status without exposing the actual API key.
    """
    
    is_configured = (
        settings.OPENAI_API_KEY and 
        settings.OPENAI_API_KEY != "sk-placeholder" and
        len(settings.OPENAI_API_KEY) > 20
    )
    
    return {
        "configured": is_configured,
        "key_length": len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0,
        "key_prefix": settings.OPENAI_API_KEY[:7] if is_configured else "not-set",
        "message": "OpenAI is properly configured" if is_configured else "OpenAI API key not configured or invalid"
    }

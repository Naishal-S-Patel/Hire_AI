"""
Application management endpoints — users apply, HR reviews.
"""

import hashlib
import logging
import os
from typing import List, Optional
from uuid import UUID

import aiofiles
import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.openai_service import generate_ai_summary
from app.db import get_db
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────────────


class ApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    job_title: Optional[str]
    candidate_name: Optional[str]
    candidate_email: Optional[str]
    candidate_phone: Optional[str]
    experience_years: Optional[float]
    skills: List[str]
    ats_score: Optional[float]
    risk_score: Optional[float]
    ai_summary: Optional[str]
    status: str
    source: str
    created_at: str

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: str  # PENDING | SHORTLISTED | ACCEPTED | REJECTED


# ── Helpers ──────────────────────────────────────────────────────────────────


async def parse_resume_via_ml(file_path: str) -> dict:
    """Call ML service to parse resume."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/pdf")}
            response = await client.post(
                f"{settings.ML_SERVICE_URL}/parse_resume",
                files=files
            )
            response.raise_for_status()
            return response.json()


def calculate_ats_score(candidate_skills: List[str], candidate_exp: float, job: Job) -> float:
    """Calculate ATS score based on job requirements."""
    skill_match_weight = 0.5
    experience_weight = 0.3
    education_weight = 0.2
    
    # Skill matching
    required_skills = set(s.lower() for s in (job.required_skills or []))
    candidate_skills_lower = set(s.lower() for s in candidate_skills)
    
    if required_skills:
        skill_match = len(required_skills & candidate_skills_lower) / len(required_skills)
    else:
        skill_match = 0.5
    
    # Experience matching
    if job.experience_required and candidate_exp is not None:
        if candidate_exp >= job.experience_required:
            exp_match = 1.0
        else:
            exp_match = candidate_exp / job.experience_required
    else:
        exp_match = 0.5
    
    # Education (simplified - always 0.5 for now)
    edu_match = 0.5
    
    score = (
        skill_match * skill_match_weight +
        exp_match * experience_weight +
        edu_match * education_weight
    ) * 100
    
    return min(100, max(0, score))


def calculate_risk_score(skills: List[str], experience: float, resume_hash: str, db_session) -> float:
    """Calculate fraud/risk score."""
    risk = 0
    
    # Rule 1: 0 experience but >15 skills = MEDIUM risk
    if experience == 0 and len(skills) > 15:
        risk += 20
    
    # Rule 2: Duplicate resume hash = HIGH risk (would need async check)
    # Simplified for now
    
    return min(100, risk)


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_application(
    job_id: UUID = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Submit job application (public endpoint for users)."""
    
    # Verify job exists
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Save uploaded file
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOADS_DIR, f"{email}_{file.filename}")
    
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    
    # Calculate resume hash
    resume_hash = hashlib.sha256(content).hexdigest()
    
    # Parse resume via ML service
    try:
        parsed_data = await parse_resume_via_ml(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {str(e)}")
    
    # Extract data
    skills = parsed_data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split() if s.strip()]
    
    experience_years = float(parsed_data.get("experience_years", 0))
    resume_text = parsed_data.get("resume_text", "")
    education = parsed_data.get("education", [])
    
    # Generate AI summary
    ai_summary = await generate_ai_summary(
        resume_text=resume_text,
        skills=skills,
        experience_years=experience_years,
        name=name
    )
    
    # Calculate ATS score
    ats_score = calculate_ats_score(skills, experience_years, job)
    
    # Calculate risk score
    risk_score = calculate_risk_score(skills, experience_years, resume_hash, db)
    
    # Create or update candidate record
    result = await db.execute(select(Candidate).where(Candidate.email == email))
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        candidate = Candidate(
            full_name=name,
            email=email,
            phone=phone,
            skills=skills,
            experience_years=experience_years,
            education=education,
            resume_path=file.filename,
            resume_file_url=file_path,
            resume_text=resume_text,
            resume_hash=resume_hash,
            ai_summary=ai_summary,
            source="PORTAL",
            parsed_json=parsed_data,
        )
        db.add(candidate)
        await db.flush()
    
    # Create application
    application = Application(
        job_id=job_id,
        candidate_id=candidate.id,
        candidate_name=name,
        candidate_email=email,
        candidate_phone=phone,
        resume_file_url=file_path,
        resume_text=resume_text,
        experience_years=experience_years,
        skills=skills,
        education=education,
        ai_summary=ai_summary,
        ats_score=ats_score,
        risk_score=risk_score,
        status="PENDING",
        source="PORTAL",
    )
    
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    return ApplicationResponse(
        id=application.id,
        job_id=application.job_id,
        job_title=job.title,
        candidate_name=application.candidate_name,
        candidate_email=application.candidate_email,
        candidate_phone=application.candidate_phone,
        experience_years=float(application.experience_years) if application.experience_years else None,
        skills=application.skills or [],
        ats_score=float(application.ats_score) if application.ats_score else None,
        risk_score=float(application.risk_score) if application.risk_score else None,
        ai_summary=application.ai_summary,
        status=application.status,
        source=application.source,
        created_at=application.created_at.isoformat(),
    )


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    job_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List applications (HR sees all, users see their own)."""
    
    query = select(Application, Job).join(Job, Application.job_id == Job.id)
    
    if current_user.role == "HR":
        # HR sees all applications, optionally filtered by job or status
        if job_id:
            query = query.where(Application.job_id == job_id)
        if status_filter and status_filter != "REJECTED":
            query = query.where(Application.status == status_filter)
        elif status_filter != "REJECTED":
            query = query.where(Application.status != "REJECTED")
    else:
        # Users see only their applications
        query = query.where(Application.candidate_email == current_user.email)
    
    query = query.order_by(Application.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            job_title=job.title,
            candidate_name=app.candidate_name,
            candidate_email=app.candidate_email,
            candidate_phone=app.candidate_phone,
            experience_years=float(app.experience_years) if app.experience_years else None,
            skills=app.skills or [],
            ats_score=float(app.ats_score) if app.ats_score else None,
            risk_score=float(app.risk_score) if app.risk_score else None,
            ai_summary=app.ai_summary,
            status=app.status,
            source=app.source,
            created_at=app.created_at.isoformat(),
        )
        for app, job in rows
    ]


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get application details."""
    result = await db.execute(
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app, job = row
    
    # Authorization check
    if current_user.role != "HR" and app.candidate_email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ApplicationResponse(
        id=app.id,
        job_id=app.job_id,
        job_title=job.title,
        candidate_name=app.candidate_name,
        candidate_email=app.candidate_email,
        candidate_phone=app.candidate_phone,
        experience_years=float(app.experience_years) if app.experience_years else None,
        skills=app.skills or [],
        ats_score=float(app.ats_score) if app.ats_score else None,
        risk_score=float(app.risk_score) if app.risk_score else None,
        ai_summary=app.ai_summary,
        status=app.status,
        source=app.source,
        created_at=app.created_at.isoformat(),
    )


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: UUID,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update application status (HR only)."""
    if current_user.role != "HR":
        raise HTTPException(status_code=403, detail="Only HR can update application status")
    
    result = await db.execute(
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app, job = row
    
    # Update status and associate with HR
    app.status = status_update.status
    app.hr_id = current_user.id
    
    await db.commit()
    await db.refresh(app)
    
    return ApplicationResponse(
        id=app.id,
        job_id=app.job_id,
        job_title=job.title,
        candidate_name=app.candidate_name,
        candidate_email=app.candidate_email,
        candidate_phone=app.candidate_phone,
        experience_years=float(app.experience_years) if app.experience_years else None,
        skills=app.skills or [],
        ats_score=float(app.ats_score) if app.ats_score else None,
        risk_score=float(app.risk_score) if app.risk_score else None,
        ai_summary=app.ai_summary,
        status=app.status,
        source=app.source,
        created_at=app.created_at.isoformat(),
    )


@router.get("/{application_id}/resume")
async def get_application_resume(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream resume PDF for viewing."""
    from fastapi.responses import FileResponse
    
    result = await db.execute(select(Application).where(Application.id == application_id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Authorization
    if current_user.role != "HR" and app.candidate_email != current_user.email:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not app.resume_file_url or not os.path.exists(app.resume_file_url):
        raise HTTPException(status_code=404, detail="Resume file not found")
    
    return FileResponse(
        app.resume_file_url,
        media_type="application/pdf",
        filename=os.path.basename(app.resume_file_url)
    )

"""
Job management endpoints — HR creates jobs, users view jobs.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.job import Job
from app.models.user import User

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class JobCreate(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    required_skills: List[str] = []
    experience_required: Optional[float] = None
    company: Optional[str] = None


class JobResponse(BaseModel):
    id: UUID
    title: str
    description: str
    location: Optional[str]
    required_skills: List[str]
    experience_required: Optional[float]
    company: Optional[str]
    created_by_hr: Optional[UUID]
    created_at: str
    is_active: bool

    class Config:
        from_attributes = True


# ── Helper: optional auth ────────────────────────────────────────────────────

async def _get_optional_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Try to resolve the current user but don't fail if missing/invalid."""
    if not authorization:
        return None
    try:
        from app.routers.auth_router import verify_token
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        email = verify_token(token, expected_type="access")
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    except Exception:
        return None


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: Optional[User] = Depends(_get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job posting. Any authenticated user can create jobs."""
    new_job = Job(
        title=job_data.title,
        description=job_data.description,
        location=job_data.location,
        required_skills=job_data.required_skills,
        experience_required=job_data.experience_required,
        company=job_data.company,
        created_by_hr=current_user.id if current_user else None,
    )
    
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    return JobResponse(
        id=new_job.id,
        title=new_job.title,
        description=new_job.description,
        location=new_job.location,
        required_skills=new_job.required_skills or [],
        experience_required=float(new_job.experience_required) if new_job.experience_required else None,
        company=new_job.company,
        created_by_hr=new_job.created_by_hr,
        created_at=new_job.created_at.isoformat(),
        is_active=new_job.is_active,
    )


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all active jobs (public endpoint)."""
    result = await db.execute(
        select(Job)
        .where(Job.is_active == True)
        .order_by(Job.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    
    return [
        JobResponse(
            id=job.id,
            title=job.title,
            description=job.description,
            location=job.location,
            required_skills=job.required_skills or [],
            experience_required=float(job.experience_required) if job.experience_required else None,
            company=job.company,
            created_by_hr=job.created_by_hr,
            created_at=job.created_at.isoformat(),
            is_active=job.is_active,
        )
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get job details by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        location=job.location,
        required_skills=job.required_skills or [],
        experience_required=float(job.experience_required) if job.experience_required else None,
        company=job.company,
        created_by_hr=job.created_by_hr,
        created_at=job.created_at.isoformat(),
        is_active=job.is_active,
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: UUID,
    current_user: Optional[User] = Depends(_get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.is_active = False
    await db.commit()
